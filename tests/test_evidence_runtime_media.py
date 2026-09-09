import copy
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import unittest
import subprocess

from test_planning import ROOT, SKILL, profile
from vge_core import ContractError, digest, file_hash, load
from vge_evidence import aggregate, validate_observation, lifecycle
from vge_runtime import ComfyClient, validate_workflow, bind_workflow, submit, poll, collect, resource_status, workflow_fingerprint, validate_profile_runtime
from vge_media import run, probe, assemble, contact_sheet, validate_assembly_manifest


def evidence(path):
    now=datetime.now(timezone.utc)
    before=(now-timedelta(seconds=2)).isoformat()
    attempt={'schema_version':1,'id':'attempt_1','execution_plan_ref':'exec_1','shot_id':'shot_1','attempt_index':1,
             'status':'SUCCEEDED','started_at':before,'ended_at':before,'profile':{'id':'profile_1','revision':1},
             'model':{'id':'model_1','version':'1','asset_hash':file_hash(path)},
             'runtime':{'provider':'test','endpoint':'local','version':'1','node_inventory_hash':digest({})},
             'workflow':{'ref':'workflow.json','queue_id':'queue_1','content_hash':digest({})},
             'nodes':[{'id':'1','type':'fixture','version':'1'}], 'inputs':[], 'parameters':{'seed':1}, 'progress_ref':'events.jsonl','unknown_fields':[]}
    attempt['shot_contract_hash']=digest({'id':'shot_1','revision':1,'acceptance_ids':['QG-17']})
    artifact={'schema_version':1,'id':'art_1','shot_id':'shot_1','execution_attempt_ref':'attempt_1','artifact_ref':str(path),
              'content_hash':file_hash(path),'collected_at':before,'generation_status':'GENERATED',
            'media':{'kind':'video'},'runtime':{'workflow_hash':digest({})},
              'quality_review':{'lifecycle':'COMPLETE','observation_ref':'obs_1'}}
    observation={'id':'obs_1','shot_id':'shot_1','generation_artifact_ref':'art_1','artifact_ref':str(path),'observed_content_hash':file_hash(path),
                 'observed_at':now.isoformat(),'procedure':'Test fixture byte inspection, not media judgment','status':'PASS',
                 'checks':[{'id':'QG-17','required':True,'result':'PASS','evidence':'test file bytes'}],'limitations':['Synthetic fixture'],'repair_route':'shot_1'}
    return {'attempt':attempt,'artifact':artifact,'observation':observation,
            'shot':{'id':'shot_1','revision':1,'acceptance_ids':['QG-17']},'required_checks':['QG-17']}


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'video.dat';self.path.write_bytes(b'first version')
        self.e=evidence(self.path)
    def accept(self):return validate_observation(self.e['observation'],self.e['artifact'],self.e['attempt'],self.e['shot'])
    def test_current_linked_observation_accepted(self):self.assertTrue(self.accept()['accepted'])
    def test_overwritten_path_stales_qa(self):
        self.path.write_bytes(b'second version')
        with self.assertRaisesRegex(ContractError,'changed'):self.accept()
    def test_missing_required_check_cannot_pass(self):
        self.e['shot']['acceptance_ids'].append('QG-05')
        with self.assertRaises(ContractError):self.accept()
    def test_optional_cannot_replace_required_check(self):
        self.e['observation']['checks'][0]['required']=False
        with self.assertRaises(ContractError):self.accept()
    def test_empty_required_set_cannot_pass(self):
        self.e['shot']['acceptance_ids']=[]
        with self.assertRaises(ContractError):self.accept()
    def test_acceptance_requires_canonical_shot_not_caller_gates(self):
        with self.assertRaises(ContractError):
            validate_observation(self.e['observation'],self.e['artifact'],self.e['attempt'],['QG-17'])
    def test_acceptance_binds_shot_revision_and_gate_set_to_attempt(self):
        forged={'id':'shot_1','revision':1,'acceptance_ids':['QG-01']}
        with self.assertRaisesRegex(ContractError,'immutable execution attempt'):
            validate_observation(self.e['observation'],self.e['artifact'],self.e['attempt'],forged)
    def test_shot_attempt_hash_and_artifact_mismatch(self):
        for owner,field,value in [('artifact','execution_attempt_ref','wrong'),('artifact','shot_id','wrong'),('observation','observed_content_hash',digest('wrong')),('observation','generation_artifact_ref','wrong')]:
            with self.subTest(field=field):
                self.e=evidence(self.path);self.e[owner][field]=value
                with self.assertRaises(ContractError):self.accept()
    def test_unknown_provenance_blocks(self):
        self.e['attempt']['unknown_fields']=['parameters.seed']
        with self.assertRaises(ContractError):self.accept()
    def test_future_observation_blocks(self):
        self.e['observation']['observed_at']=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()
        with self.assertRaises(ContractError):self.accept()
    def test_pending_does_not_regress_lifecycle(self):
        for state in ['PLANNED','READY','RUNNING','GENERATED','REVIEW','ACCEPTED']:
            self.assertEqual(state,lifecycle(state,'NOT_RUN'))
        with self.assertRaises(ContractError):lifecycle('PLANNED','QA_PASS')
    def test_aggregate_required_partial_and_missing_procedure(self):
        checks=self.e['observation']['checks']
        for status in ['PARTIAL','FAIL','BLOCKED','NOT_RUN']:
            checks[0]['result']=status;self.assertEqual(status,aggregate(checks,'art_1'))
        self.e['observation']['procedure']=None
        with self.assertRaises(ContractError):self.accept()
    def test_aggregate_optional_incomplete_not_silently_omitted(self):
        checks=self.e['observation']['checks']+[{'id':'optional','required':False,'result':'NOT_RUN'}]
        self.assertEqual('PARTIAL',aggregate(checks))
    def test_all_empty_not_applicable_not_pass(self):
        self.assertEqual('NOT_RUN',aggregate([]))
        self.assertEqual('BLOCKED',aggregate([{'id':'g','required':True,'result':'NOT_APPLICABLE','reason':'test'}]))
    def test_waiver_scope_and_expiry(self):
        check=self.e['observation']['checks'][0];check['result']='WAIVED'
        check['waiver']={'reason':'fixture','authority':'test-human','expires_at':'2099-01-01T00:00:00Z','scope':{'artifact_id':'art_1','check_id':'QG-17'}}
        self.assertEqual('PASS',aggregate([check],'art_1'))
        self.assertEqual('BLOCKED',aggregate([check],'art_other'))
        check['waiver']['expires_at']='2000-01-01T00:00:00Z';self.assertEqual('BLOCKED',aggregate([check],'art_1'))
    def test_forged_aggregate_rejected(self):
        self.e['observation']['checks'][0]['result']='PARTIAL'
        with self.assertRaisesRegex(ContractError,'aggregate'):self.accept()
    def test_cli_accept_nonpass_is_nonzero(self):
        self.e['observation']['checks'][0]['result']='PARTIAL'
        self.e['observation']['status']='PARTIAL'
        path=Path(self.tmp.name)/'bundle.json';path.write_text(json.dumps(self.e))
        result=subprocess.run([sys.executable,str(SKILL/'scripts/vge.py'),'accept',str(path)],cwd=self.tmp.name,capture_output=True,text=True)
        self.assertEqual(2,result.returncode)
        self.assertEqual('PARTIAL',json.loads(result.stdout)['status'])


NODE_INFO={'Source':{'input':{'required':{'model_name':[['model.bin']], 'width':['INT',{'min':32,'max':512}]}},'output':['IMAGE']},
           'Save':{'input':{'required':{'images':['IMAGE'], 'filename_prefix':['STRING']}},'output':[],'output_node':True}}
WORKFLOW={'1':{'class_type':'Source','inputs':{'model_name':'model.bin','width':64}},
          '2':{'class_type':'Save','inputs':{'images':['1',0],'filename_prefix':'test'}}}

DYNAMIC_NODE_INFO={
    'VideoSource': {'input': {'required': {}, 'optional': {}}, 'output': ['VIDEO']},
    'SaveVideo': {
        'input': {
            'required': {
                'video': ['VIDEO'],
                'format': ['COMFY_DYNAMICCOMBO_V3', {'options': [
                    {'key': 'mp4', 'inputs': {'required': {
                        'codec': ['COMFY_DYNAMICCOMBO_V3', {'options': [
                            {'key': 'auto', 'inputs': {'required': {}}},
                            {'key': 'h264', 'inputs': {'required': {}, 'optional': {
                                'encoding': ['COMFY_DYNAMICCOMBO_V3', {'options': [
                                    {'key': 'auto', 'inputs': {'required': {}}},
                                    {'key': 're-encode', 'inputs': {'required': {
                                        'crf': ['FLOAT', {'min': 0.0, 'max': 51.0}]
                                    }}}
                                ]}]
                            }}}
                        ]}]
                    }}}
                ]}]
            },
            'optional': {}
        },
        'output': [],
        'output_node': True,
    },
}

DYNAMIC_WORKFLOW={
    '1': {'class_type': 'VideoSource', 'inputs': {}},
    '2': {'class_type': 'SaveVideo', 'inputs': {
        'video': ['1', 0], 'format': 'mp4', 'format.codec': 'auto'
    }},
}


class GraphTests(unittest.TestCase):
    def test_valid_graph(self):self.assertEqual('PASS',validate_workflow(WORKFLOW,NODE_INFO)['status'])
    def test_bad_graph_mutations(self):
        cases=[]
        w=copy.deepcopy(WORKFLOW);w['1']['class_type']='Missing';cases.append(w)
        w=copy.deepcopy(WORKFLOW);w['1']['inputs']['model_name']='absent.bin';cases.append(w)
        w=copy.deepcopy(WORKFLOW);w['1']['inputs']['width']=True;cases.append(w)
        w=copy.deepcopy(WORKFLOW);w['1']['inputs']['width']=1000;cases.append(w)
        w=copy.deepcopy(WORKFLOW);w['2']['inputs']['images']=['1',3];cases.append(w)
        w=copy.deepcopy(WORKFLOW);w['2']['inputs']['images']=['404',0];cases.append(w)
        w=copy.deepcopy(WORKFLOW);w['1']['inputs']['model_name']=['1',0];cases.append(w)
        w=copy.deepcopy(WORKFLOW);del w['1']['inputs']['width'];cases.append(w)
        for w in cases:
            with self.subTest(w=w):self.assertEqual('FAIL',validate_workflow(w,NODE_INFO)['status'])
    def test_type_mismatch_and_cycle(self):
        w=copy.deepcopy(WORKFLOW);w['1']['inputs']['width']=['1',0]
        errors=validate_workflow(w,NODE_INFO)['issues'];self.assertTrue(any('cycle' in e for e in errors));self.assertTrue(any('type mismatch' in e for e in errors))
    def test_binding_preserves_source_and_records_changes(self):
        b=bind_workflow(WORKFLOW,[{'node_id':'1','input':'width','value':128,'source':'user'}],NODE_INFO)
        self.assertEqual(64,WORKFLOW['1']['inputs']['width']);self.assertEqual(128,b['workflow']['1']['inputs']['width']);self.assertEqual(64,b['changes'][0]['previous'])
    def test_unknown_bindings_and_ui_export_fail(self):
        with self.assertRaises(ContractError):bind_workflow(WORKFLOW,[{'node_id':'3','input':'width','value':128,'source':'user'}],NODE_INFO)
        with self.assertRaises(ContractError):validate_workflow({'nodes':[]},NODE_INFO)

    def test_dynamic_combo_expands_flat_dotted_subinputs(self):
        self.assertEqual('PASS', validate_workflow(DYNAMIC_WORKFLOW, DYNAMIC_NODE_INFO)['status'])
        missing = copy.deepcopy(DYNAMIC_WORKFLOW)
        del missing['2']['inputs']['format.codec']
        report = validate_workflow(missing, DYNAMIC_NODE_INFO)
        self.assertEqual('FAIL', report['status'])
        self.assertTrue(any('format.codec' in issue for issue in report['issues']))
        invalid = copy.deepcopy(DYNAMIC_WORKFLOW)
        invalid['2']['inputs']['format.codec'] = 'h265'
        self.assertEqual('FAIL', validate_workflow(invalid, DYNAMIC_NODE_INFO)['status'])

        reencode = copy.deepcopy(DYNAMIC_WORKFLOW)
        reencode['2']['inputs'].update({'format.codec': 'h264', 'format.codec.encoding': 're-encode'})
        report = validate_workflow(reencode, DYNAMIC_NODE_INFO)
        self.assertEqual('FAIL', report['status'])
        self.assertTrue(any('format.codec.encoding.crf' in issue for issue in report['issues']))
        reencode['2']['inputs']['format.codec.encoding.crf'] = 23.0
        self.assertEqual('PASS', validate_workflow(reencode, DYNAMIC_NODE_INFO)['status'])

    def test_workflow_fingerprint_includes_dynamic_codec_selection(self):
        changed = copy.deepcopy(DYNAMIC_WORKFLOW)
        changed['2']['inputs']['format.codec'] = 'h264'
        self.assertNotEqual(workflow_fingerprint(DYNAMIC_WORKFLOW, DYNAMIC_NODE_INFO),
                            workflow_fingerprint(changed, DYNAMIC_NODE_INFO))

    def test_bundled_h3_workflows_use_current_flat_dynamic_combo_shape(self):
        workflow_dir = SKILL / 'assets' / 'workflows'
        for name in ('h3-smoke-api.json', 'h3-r2v-probe-api.json'):
            with self.subTest(name=name):
                node = json.loads((workflow_dir / name).read_text())['15']['inputs']
                self.assertEqual('mp4', node['format'])
                self.assertEqual('auto', node['format.codec'])
                self.assertNotIn('codec', node)
    def test_local_boundary_rejects_remote_credentials_and_redirects(self):
        for url in ['https://example.com','http://user:pass@127.0.0.1:8188','file:///tmp/a','http://127.0.0.1?token=x']:
            with self.subTest(url=url),self.assertRaises(ContractError):ComfyClient(url)


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.model=Path(self.tmp.name)/'model.bin';self.model.write_bytes(b'fixture model')
        owner=self;self.posts=0;self.fail=False;self.complete=True;self.cancelled=False;self.badpath=False
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                if self.path=='/system_stats':data={'system':{'comfyui_version':'1','python_version':'1','pytorch_version':'test+cu'},'devices':[{'index':0,'name':'fixture-gpu','type':'cuda','vram_total':1000,'vram_free':900}]}
                elif self.path=='/object_info':data=NODE_INFO
                elif self.path.startswith('/history/'):
                    data={'queue_1':{'prompt':[0,'queue_1',WORKFLOW,{},['2']],'status':{'completed':True,'status_str':'cancelled' if owner.cancelled else 'success'},'outputs':{'2':{'images':[{'filename':'../bad.png' if owner.badpath else 'test.png','subfolder':'','type':'output'}]}}}} if owner.complete else {}
                elif self.path.startswith('/view?'):
                    self.send_response(200);self.end_headers();self.wfile.write(b'fixture image');return
                else:self.send_response(404);self.end_headers();return
                self.send_response(200);self.end_headers();self.wfile.write(json.dumps(data).encode())
            def do_POST(self):
                owner.posts+=1
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(500 if owner.fail else 200);self.end_headers()
                if not owner.fail:self.wfile.write(b'{"prompt_id":"queue_1","node_errors":{}}')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.server.daemon_threads=True
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)
        self.client=ComfyClient(f'http://127.0.0.1:{self.server.server_port}')
        p=profile();p.update(runtime_version='1',node_inventory_hash=digest(NODE_INFO),workflow_hash=digest(WORKFLOW),model='model_1',model_asset_hash=file_hash(self.model))
        shot={'id':'shot_1','revision':1,'acceptance_ids':['QG-17'],'duration_s':5,'generation_mode':'T2V','parameters':{},'dependency_ids':[]}
        self.context={'execution_plan_ref':'exec_1','shot_id':'shot_1','attempt_index':1,'profile':{'id':p['id'],'revision':1},'profile_record':p,'shot':shot,'selected_device':'cuda:0',
                      'model':{'id':'model_1','version':'1','asset_path':str(self.model),'workflow_binding':{'node_id':'1','input':'model_name'}},'inputs':[],'parameters':{'bindings':{}},'node_versions':{'Source':'1','Save':'1'}}
    def send(self,authorized=True,probe_mode=False):return submit(self.client,WORKFLOW,self.context,Path(self.tmp.name)/'runs',authorized,probe_mode)
    def test_submit_poll_collect_real_http_boundary(self):
        submitted=self.send();self.assertEqual(1,self.posts)
        runpath=Path(submitted['run_directory']);self.assertTrue((runpath/'attempt-001.json').exists());self.assertTrue((runpath/'attempt-002.json').exists())
        events=[json.loads(line) for line in (runpath/'events.jsonl').read_text().splitlines()]
        self.assertEqual(['INTENT_RECORDED','SUBMITTED'], [event['status'] for event in events])
        history=poll(self.client,'queue_1',1,.01);self.assertEqual('SUCCEEDED',history['status'])
        artifacts=collect(self.client,submitted['attempt'],history,Path(self.tmp.name)/'artifacts')
        self.assertEqual(1,len(artifacts));self.assertEqual('NOT_STARTED',artifacts[0]['quality_review']['lifecycle'])
        self.assertEqual('image',artifacts[0]['media']['kind'])
        self.assertEqual(submitted['attempt']['shot_contract_hash'], artifacts[0]['runtime']['shot_contract_hash'])
        self.assertEqual(submitted['attempt']['profile']['content_hash'], artifacts[0]['runtime']['profile_content_hash'])
        self.assertEqual(submitted['attempt']['model']['asset_hash'], artifacts[0]['runtime']['model_asset_hash'])
        self.assertEqual(submitted['attempt']['runtime']['resource_context_hash'], artifacts[0]['runtime']['resource_context_hash'])
        self.assertEqual(submitted['attempt']['shot_contract_hash'], artifacts[0]['shot_contract_hash'])
        self.assertEqual(submitted['attempt']['profile']['content_hash'], artifacts[0]['profile_content_hash'])
        self.assertEqual(submitted['attempt']['model']['asset_hash'], artifacts[0]['model_asset_hash'])
        self.assertEqual(submitted['attempt']['inputs'], artifacts[0]['input_hashes'])
        self.assertTrue(submitted['attempt']['shot_contract_hash'].startswith('sha256:'))
        self.assertEqual(workflow_fingerprint(WORKFLOW,NODE_INFO),submitted['attempt']['workflow']['fingerprint'])
        self.assertEqual('cuda:0', submitted['attempt']['runtime']['selected_device'])
        self.assertTrue(submitted['attempt']['runtime']['resource_context_hash'].startswith('sha256:'))
        self.assertEqual('1', submitted['attempt']['runtime']['runtime_context']['python_version'])
        profile_snapshot = dict(submitted['attempt']['profile']); declared_profile_hash = profile_snapshot.pop('content_hash'); profile_snapshot.pop('revision')
        self.assertEqual(digest(profile_snapshot), declared_profile_hash)
        self.assertEqual(file_hash(artifacts[0]['artifact_ref']),artifacts[0]['content_hash'])

    def test_resource_snapshot_is_conservative(self):
        discovery={'resource_inventory':[{'id':'gpu0','vram_free':100},{'id':'gpu1','vram_free':200}]}
        self.assertEqual('SUPPORTED',resource_status(discovery,{'min_vram_bytes':150})['status'])
        self.assertEqual('BLOCKED',resource_status(discovery,{'min_vram_bytes':300})['status'])
        self.assertEqual('UNKNOWN',resource_status({'resource_inventory':[]})['status'])
        selected={'resource_inventory':[{'id':'0','device_id':'cuda:0','vram_free':100},{'id':'1','device_id':'cuda:1','vram_free':1000}]}
        self.assertEqual('BLOCKED',resource_status(selected,{'device_id':'cuda:0','min_vram_bytes':200})['status'])
    def test_selected_device_must_be_observed_before_post(self):
        self.context['selected_device'] = 'cuda:1'
        with self.assertRaisesRegex(ContractError, 'observed resource inventory'):
            self.send()
        self.assertEqual(0, self.posts)
    def test_caller_profile_hash_must_match_resolved_record(self):
        self.context['profile']['content_hash'] = digest('wrong-profile')
        with self.assertRaisesRegex(ContractError, 'Caller profile content hash'):
            self.send()
        self.assertEqual(0, self.posts)
    def test_profile_runtime_uses_external_drift_observations(self):
        p = profile()
        resources = [{'id': '0', 'device_id': 'cuda:0', 'type': 'cuda', 'vram_total': 1000}]
        p.update(workflow_hash=digest(WORKFLOW), workflow_fingerprint=workflow_fingerprint(WORKFLOW, NODE_INFO),
                 node_inventory_hash=digest(NODE_INFO), model_asset_hash=digest('model'), selected_device='cuda:0',
                 resource_context_hash=digest(resources), runtime_commit='c1', runtime_dirty=False, custom_node_commits={'pack': 'v1'})
        discovery = {'runtime_version': '1', 'node_inventory_hash': digest(NODE_INFO), 'resource_inventory': resources,
                     'runtime_context': {'runtime_commit': 'c2', 'runtime_dirty': True, 'custom_node_commits': {'pack': 'v2'}},
                     'model_asset_hash': digest('different-model'), 'object_info': NODE_INFO}
        result = validate_profile_runtime(p, discovery, WORKFLOW)
        self.assertEqual('EXPIRED', result['status'])
        self.assertIn('model asset changed', result['expiration_triggers'])
        self.assertIn('runtime commit changed', result['expiration_triggers'])
        self.assertIn('custom-node commits changed', result['expiration_triggers'])
    def test_authorization_before_any_post(self):
        with self.assertRaises(ContractError):self.send(False)
        self.assertEqual(0,self.posts)
    def test_forged_compatibility_does_not_bypass(self):
        self.context['compatibility']={'status':'SUPPORTED'};self.context['profile_record']['status']='UNKNOWN'
        with self.assertRaises(ContractError):self.send()
        self.assertEqual(0,self.posts)
    def test_missing_dependency_blocks_before_post(self):
        self.context['shot']['dependency_ids']=['shot_previous']
        with self.assertRaises(ContractError):self.send()
        self.assertEqual(0,self.posts)
    def test_loose_observed_state_cannot_authorize_dependency(self):
        bundle=evidence(self.model);bundle['observed_end_state']={'door':'open'}
        self.context['shot'].update(id='shot_next',dependency_ids=['shot_1'],start_state_delta={})
        self.context.update(shot_id='shot_next',expected_start_state={'door':'open'},accepted_dependencies=[bundle])
        with self.assertRaises(ContractError):self.send()
        self.assertEqual(0,self.posts)
    def test_hash_bound_state_required_even_with_empty_start_delta(self):
        bundle=evidence(self.model);bundle['observation']['checks'].append({'id':'QG-07','required':True,'result':'PASS','evidence':'fixture state inspected'})
        bundle['required_checks'].append('QG-07');bundle['observation']['observed_end_state']={'door':'closed'}
        self.context['shot'].update(id='shot_next',dependency_ids=['shot_1'],start_state_delta={})
        self.context.update(shot_id='shot_next',expected_start_state={'door':'open'},accepted_dependencies=[bundle])
        with self.assertRaisesRegex(ContractError,'state mismatch'):self.send()
        self.assertEqual(0,self.posts)
    def test_forged_recorded_parameters_blocked(self):
        self.context['parameters']={'bindings':{'width':512}}
        with self.assertRaisesRegex(ContractError,'parameter bindings'):self.send()
        self.assertEqual(0,self.posts)
    def test_unbound_seed_not_recorded_as_fact(self):
        self.context['parameters']['seed']=1
        with self.assertRaisesRegex(ContractError,'seed'):self.send()
        self.assertEqual(0,self.posts)
    def test_primary_model_requires_matching_workflow_binding(self):
        self.context['model']['workflow_binding']['input']='missing'
        with self.assertRaisesRegex(ContractError,'model'):self.send()
        self.assertEqual(0,self.posts)
    def test_collection_never_promotes_terminal_failure(self):
        submitted=self.send();history=poll(self.client,'queue_1',1,.01)
        for status in ['FAILED','CANCELLED','UNKNOWN']:
            with self.subTest(status=status):
                submitted['attempt']['status']=status
                with self.assertRaises(ContractError):collect(self.client,submitted['attempt'],history,Path(self.tmp.name)/'artifacts')
    def test_collection_checks_sealed_graph_in_actual_history(self):
        submitted=self.send();history=poll(self.client,'queue_1',1,.01)
        history['history']['prompt'][2]=copy.deepcopy(WORKFLOW);history['history']['prompt'][2]['1']['inputs']['width']=512
        with self.assertRaisesRegex(ContractError,'sealed workflow'):collect(self.client,submitted['attempt'],history,Path(self.tmp.name)/'artifacts')
    def test_profile_workflow_inventory_and_model_drift_block(self):
        for key in ['workflow_hash','node_inventory_hash','model_asset_hash']:
            with self.subTest(key=key):
                prior=self.context['profile_record'][key];self.context['profile_record'][key]=digest('wrong')
                with self.assertRaises(ContractError):self.send()
                self.context['profile_record'][key]=prior
        self.assertEqual(0,self.posts)
    def test_uncertain_submission_journal_no_retry(self):
        self.fail=True
        with self.assertRaises(ContractError):self.send()
        self.assertEqual(1,self.posts)
        paths=list((Path(self.tmp.name)/'runs').glob('*/submission-uncertain.json'));self.assertEqual(1,len(paths))
        self.assertEqual('UNKNOWN',load(paths[0])['status'])
    def test_timeout_does_not_resubmit(self):
        self.complete=False;result=poll(self.client,'queue_1',.03,.01)
        self.assertEqual('UNKNOWN',result['status']);self.assertEqual(0,self.posts)
    def test_cancelled_history_is_not_success(self):
        self.cancelled=True
        result=poll(self.client,'queue_1',1,.01)
        self.assertEqual('CANCELLED',result['status'])
    def test_collection_rejects_traversal(self):
        submitted=self.send();self.badpath=True;history=poll(self.client,'queue_1',1,.01)
        with self.assertRaises(ContractError):collect(self.client,submitted['attempt'],history,Path(self.tmp.name)/'outputs')
    def test_diagnostic_probe_is_explicit_and_scoped(self):
        self.context['profile_record']['status']='PROPOSED'
        with self.assertRaises(ContractError):self.send(probe_mode=True)
        self.context.update(probe_purpose='fixture model test',probe_budget={'max_submissions':1})
        self.assertEqual('CAPABILITY_PROBE',self.send(probe_mode=True)['attempt']['purpose'])
    def test_probe_can_establish_missing_profile_hashes(self):
        self.context['profile_record']['status']='PROPOSED'
        for key in ('runtime_version','workflow_hash','node_inventory_hash','model_asset_hash'):
            self.context['profile_record'][key]='UNKNOWN' if key == 'runtime_version' else None
        self.context.update(probe_purpose='establish missing profile bindings',probe_budget={'max_submissions':1})
        result=self.send(probe_mode=True)
        self.assertEqual('CAPABILITY_PROBE',result['attempt']['purpose'])
        self.assertEqual(1,self.posts)


class MediaTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(shutil.which('ffmpeg'),'FFmpeg required for this suite')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)
        self.video=self.path/'source with spaces.mp4'
        run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','testsrc2=size=64x64:rate=24:duration=1','-c:v','libx264','-pix_fmt','yuv420p',str(self.video)])
        first=evidence(self.video)
        second=copy.deepcopy(first)
        second['attempt']['id']='attempt_2'
        second['attempt']['shot_id']='shot_2'
        second['shot']['id']='shot_2'
        second['attempt']['shot_contract_hash']=digest(second['shot'])
        second['artifact']['id']='art_2'
        second['artifact']['shot_id']='shot_2'
        second['artifact']['execution_attempt_ref']='attempt_2'
        second['observation']['id']='obs_2'
        second['observation']['shot_id']='shot_2'
        second['observation']['generation_artifact_ref']='art_2'
        second['required_checks']=['QG-17']
        self.manifest={'schema_version':1,'id':'assembly_fixture','fps':24,'target_duration_s':2,
                       'shot_order':['shot_1','shot_2'],'segments':[]}
        for bundle in (first, second):
            inspection=probe(self.video)
            self.manifest['segments'].append({
                'shot_id':bundle['shot']['id'],'artifact':bundle['artifact'],
                'attempt':bundle['attempt'],'shot':bundle['shot'],
                'observation':bundle['observation'],
                'duration_s':inspection['duration_s'],'fps':inspection['fps'],
                'resolution':{'width':inspection['video_streams'][0]['width'],'height':inspection['video_streams'][0]['height']},
                'audio_source':'NONE','transition':{'status':'NONE'},
                'source_attempt':{'id':bundle['attempt']['id']},'repair_lineage':[]})
    def test_preview_assembly_and_real_probe(self):
        result=assemble(self.manifest,self.path/'preview.mp4',preview=True)
        self.assertEqual('NOT_RUN',result['editorial_acceptance']);self.assertEqual('PREVIEW',result['kind'])
        self.assertAlmostEqual(2,result['artifact']['duration_s'],places=2)
        self.assertEqual('h264',result['artifact']['video_streams'][0]['codec_name'])
        self.assertTrue(result['final_artifact_binding']['source_shots'])
    def test_final_rejects_missing_segment_qa(self):
        del self.manifest['segments'][0]['observation']
        with self.assertRaises((KeyError,ContractError)):assemble(self.manifest,self.path/'final.mp4')
    def test_accepted_segments_still_need_editorial_review(self):
        result=assemble(self.manifest,self.path/'final.mp4')
        self.assertEqual('SEGMENTS_ACCEPTED',result['generation_acceptance']);self.assertEqual('NOT_RUN',result['editorial_acceptance'])
    def test_stale_source_and_wrong_fps_rejected(self):
        self.manifest['fps']=30
        with self.assertRaises(ContractError):assemble(self.manifest,self.path/'bad.mp4',True)
        self.manifest['fps']=24;self.video.write_bytes(b'changed')
        with self.assertRaises(ContractError):assemble(self.manifest,self.path/'bad.mp4',True)

    def test_strict_assembly_manifest_rejects_missing_duplicate_or_unbound_fields(self):
        with self.assertRaisesRegex(ContractError,'shot_order'):
            validate_assembly_manifest({**self.manifest, 'shot_order': ['shot_1']})
        duplicate=copy.deepcopy(self.manifest)
        duplicate['segments'][1]['shot_id']='shot_1'
        with self.assertRaisesRegex(ContractError,'duplicated|Duplicate'):
            validate_assembly_manifest(duplicate)
        missing=copy.deepcopy(self.manifest)
        missing['segments'][0].pop('repair_lineage')
        with self.assertRaisesRegex(ContractError,'repair_lineage'):
            validate_assembly_manifest(missing)
        unbound=copy.deepcopy(self.manifest)
        unbound['segments'][1]['source_attempt']['id']='attempt_wrong'
        with self.assertRaisesRegex(ContractError,'not bound'):
            validate_assembly_manifest(unbound)
    def test_mux_audio_and_alignment(self):
        audio=self.path/'audio.wav';run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','sine=frequency=440:duration=2',str(audio)])
        self.manifest['audio_path']=str(audio)
        for segment in self.manifest['segments']:
            segment['audio_source']='MASTER_TRACK'
        result=assemble(self.manifest,self.path/'sound.mp4',True);self.assertEqual('aac',result['artifact']['audio_streams'][0]['codec_name'])
    def test_contact_sheet(self):
        result=contact_sheet(self.video,self.path/'frames.jpg',4)
        self.assertTrue(Path(result['contact_sheet']).is_file())


if __name__=='__main__':unittest.main()
