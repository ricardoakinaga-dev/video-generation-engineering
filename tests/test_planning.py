import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/video-generation-engineering'
sys.path.insert(0, str(SKILL / 'scripts'))
from vge_core import ContractError, prepare, validate, compile_plan, duration_floor, ordered, negotiate, load, save


def treatment():
    return json.loads((SKILL/'assets/templates/treatment.json').read_text())


def profile():
    return {'schema_version': 1, 'id': 'profile_test', 'provider': 'fixture', 'runtime': 'fixture-runtime',
            'runtime_version': '1', 'model': 'fixture-model', 'integration_version': '1', 'profile_revision': 1, 'status': 'CONFIRMED',
            'evidence_refs': ['test-source', 'test-probe'],
            'supports': {'modes': ['T2V'], 'inputs': ['text'], 'outputs': ['video'], 'audio': {'status': 'UNKNOWN'},
                         'camera_controls': {'status': 'UNKNOWN'}, 'identity_conditioning': 'UNKNOWN'},
            'controls': ['width','height','fps','frame_count','seed'],
            'limits': {'duration_s': {'min':1,'max':10}, 'frame_count': {'multiple':4,'offset':1},
                       'resolution': {'width': {'min':64,'max':512,'multiple':32}, 'height': {'min':64,'max':512,'multiple':32}}, 'fps':[24]},
            'validity': {'expires_at':'2099-01-01T00:00:00+00:00'},
            'feature_evidence': {'text_to_video': {'status':'CONFIRMED','source_ref':'test-source','probe_ref':'test-probe','scope':'fixture','checked_at':'2026-09-08'}}}


class PlanningTests(unittest.TestCase):
    def setUp(self): self.t = treatment()
    def assert_issue(self, plan, code):
        self.assertIn(code, [i['id'] for i in validate(plan)['issues']])
    def test_prepare_compile_real_boundary(self):
        p = prepare(self.t)
        self.assertEqual('PASS', p['validation']['status'])
        self.assertEqual('open',p['continuity_states'][0]['end_state']['vehicle_van.door'])
        self.assertEqual(p, prepare(self.t))
        c = compile_plan(p)['prompts'][0]
        self.assertEqual(10,len(c['mappings']))
        self.assertEqual([],c['omissions'])
        self.assertEqual(self.t['scene_intent']['hard_constraints'], c['sections']['constraints']['hard'])
        self.assertEqual(self.t['scene_intent'], c['sections']['setting_and_time']['scene_intent'])
        self.assertEqual(self.t['scene_bible']['relationships'], c['sections']['subject_and_identity']['relationships'])
    def test_duration_boundaries(self):
        for value, count in [(0.1,1),(30,1),(30.01,2),(45,2),(45.01,5),(59.99,5),(60,7),(90,11),(120,11)]:
            with self.subTest(value=value): self.assertEqual(count,len(duration_floor(value)))
        for value in [0,-1,True,121,float('nan'),float('inf'),'60']:
            with self.subTest(value=value),self.assertRaises(ContractError): duration_floor(value)
    def test_floor_enforced_after_preparation(self):
        self.t['scene_intent']['duration']['target_seconds']=60
        self.t['shots'][0]['duration_s']=60
        p=prepare(self.t); self.assertEqual('PASS',p['validation']['status'])
        del p['generation_strategy']; self.assert_issue(p,'DURATION_FLOOR')
    def test_ninety_second_floor_is_explicit_and_complete(self):
        self.t['scene_intent']['duration']['target_seconds']=90
        self.t['shots'][0]['duration_s']=90
        p=prepare(self.t)
        self.assertEqual('PASS',p['validation']['status'])
        for field in ('alternative_branches','recovery_checkpoints','provenance_manifest','human_checkpoints'):
            self.assertTrue(p[field])
    def test_invalid_graphs(self):
        for shots in [[{'id':'s','dependency_ids':['missing']}],[{'id':'s','dependency_ids':['s']}],[{'id':'s'},{'id':'s'}]]:
            with self.subTest(shots=shots),self.assertRaises(ContractError): ordered(shots)
    def test_order_is_stable_and_dependencies_first(self):
        self.assertEqual(['a','b','c'],ordered([{'id':'c','dependency_ids':['a','b']},{'id':'b'},{'id':'a'}]))
    def test_explicit_unknown_blocks_readiness(self):
        self.t['scene_bible']['initial_state']['vehicle_van']['position']='UNKNOWN'
        p=prepare(self.t); self.assert_issue(p,'UNRESOLVED_STATE')
        p['shots'][0]['lifecycle_status']='READY'; self.assert_issue(p,'UNRESOLVED_STATE')
        with self.assertRaises(ContractError): compile_plan(p)
    def test_unknown_resulting_state_blocks_compilation(self):
        self.t['shots'][0]['state_changes'][-1]['next']='UNKNOWN'
        p=prepare(self.t);self.assert_issue(p,'UNRESOLVED_END_STATE')
        with self.assertRaises(ContractError):compile_plan(p)
    def test_model_unknown_at_intake_does_not_block_plan(self):
        self.assertEqual('PASS',prepare(self.t)['validation']['status'])
    def test_start_state_contradiction(self):
        p=prepare(self.t);p['shots'][0]['start_state_delta']={'vehicle_van.door':'open'}
        self.assert_issue(p,'START_CONTRADICTION')
    def test_change_requires_prior_and_cause(self):
        for field,value,code in [('prior','open','DELTA_PRECONDITION'),('cause','magic','MISSING_CAUSE')]:
            p=prepare(self.t);p['shots'][0]['state_changes'][1][field]=value
            self.assert_issue(p,code)
    def test_end_state_cannot_invent_an_event(self):
        p=prepare(self.t);p['shots'][0]['end_state_delta']['vehicle_van.ignition']='ON'
        self.assert_issue(p,'END_CONTRADICTION')
    def test_diamond_conflict_not_last_writer_wins(self):
        a=copy.deepcopy(self.t['shots'][0]);a.update(id='a',duration_s=2)
        b=copy.deepcopy(a);b.update(id='b',state_changes=[],end_state_delta={})
        c=copy.deepcopy(b);c.update(id='c',dependency_ids=['a','b'])
        self.t['shots']=[a,b,c]
        self.assert_issue(prepare(self.t),'MERGE_CONFLICT')
    def test_observed_state_not_promoted_from_plan(self):
        p=prepare(self.t);p['continuity_states'][0]['state_channel']='OBSERVED'
        self.assert_issue(p,'LEDGER_DRIFT')
    def test_forged_derived_state_rejected(self):
        p=prepare(self.t);p['continuity_states'][0]['end_state']['vehicle_van.door']='closed'
        self.assert_issue(p,'LEDGER_DRIFT')
    def test_forged_graph_rejected(self):
        p=prepare(self.t);p['shot_graph']['nodes']=['wrong'];self.assert_issue(p,'GRAPH_DRIFT')
    def test_reference_conflict(self):
        self.t['reference_conflicts']=[{'id':'conflict_1','status':'OPEN','precedence':'UNRESOLVED'}]
        self.assert_issue(prepare(self.t),'REFERENCE_CONFLICT')
    def test_reference_roles_and_consent(self):
        self.t['references']=[{'id':'ref_person','roles':[],'maps_to':['unknown'],'sensitive':True,'provenance':{'consent_status':'UNKNOWN'}}]
        p=prepare(self.t); self.assert_issue(p,'REFERENCE_ROLE'); self.assert_issue(p,'RIGHTS')
    def test_identity_role_requires_explicit_rights_and_consent(self):
        self.t['references']=[{'id':'ref_face','roles':['face'],'maps_to':['subject_courier'],'provenance':{}}]
        p=prepare(self.t)
        rights=[i for i in p['validation']['issues'] if i['id']=='RIGHTS']
        self.assertEqual(2,len(rights))
    def test_lock_requires_anchor_and_observation(self):
        self.t['retention_rules']=[{'entity_id':'vehicle_van','property':'door','policy':'LOCKED'}]
        p=prepare(self.t);self.assert_issue(p,'LOCK_WITHOUT_QA');self.assert_issue(p,'LOCK_CHANGED')
    def test_no_execution_or_accepted_from_plan(self):
        p=prepare(self.t);p['execution_mode']='LOCAL_EXECUTE';self.assert_issue(p,'MODE_BOUNDARY')
        p['shots'][0]['lifecycle_status']='ACCEPTED';self.assert_issue(p,'STATE_CHANNEL')
    def test_camera_axis_requires_motivation(self):
        p=prepare(self.t);p['shots'][0]['camera']['axis_policy']='CROSS_AXIS';self.assert_issue(p,'AXIS')
    def test_duration_and_assembly_mismatch(self):
        p=prepare(self.t);p['assembly_plan']['shot_ids']=[]; self.assert_issue(p,'ASSEMBLY_ORDER')
        p['shots'][0]['duration_s']=2;self.assert_issue(p,'TOTAL_DURATION')
    def line(self):
        return {'id':'line_1','shot_id':'shot_001','speaker':'subject_courier','text':'Ready.','start_s':1,'end_s':3}
    def test_dialogue_missing_and_reaction_order(self):
        self.t['scene_intent']['dialogue_required']=True
        self.assert_issue(prepare(self.t),'DIALOGUE_MISSING')
        line=self.line();line['reaction_at_s']=2;self.t['dialogue_timeline']=[line]
        self.assert_issue(prepare(self.t),'REACTION_ORDER')
        line['intentional_overlap']=True;self.assertNotIn('REACTION_ORDER',[i['id'] for i in prepare(self.t)['validation']['issues']])
    def test_dialogue_overlap_and_invalid_speaker(self):
        one=self.line();two={**one,'id':'line_2','start_s':2,'end_s':4}
        self.t['dialogue_timeline']=[one,two];self.assert_issue(prepare(self.t),'SPEECH_OVERLAP')
        one['speaker']='missing';self.assert_issue(prepare(self.t),'SPEAKER')
    def test_visible_speech_needs_audio_and_sync(self):
        self.t['dialogue_timeline']=[{**self.line(),'visible_speech':True}]
        self.assert_issue(prepare(self.t),'LIP_SYNC_PATH')
    def test_routing_accounts_for_dialogue_and_camera_load(self):
        self.t['contact_graphs']=[]
        self.t['shots'][0].pop('contact_graph_ref')
        self.t['shots'][0]['constraints']=[]
        self.t['scene_bible']['entities'].append({'id':'subject_listener','type':'character','description':'Fictional listener','permanence':'PERSISTENT'})
        self.t['dialogue_timeline']=[{**self.line(),'listener':'subject_listener'}]
        plan=prepare(self.t)
        self.assertEqual('PRODUCTION',plan['presentation_mode'])
        self.assertEqual('complexity_routing',plan['decision_diagnostics'][0]['stage'])
        for key in ('decision_id','input_scope','result','reasons','evidence_refs','alternatives','next_action','confidence','limitations'):
            self.assertIn(key,plan['decision_diagnostics'][0])
        self.t['dialogue_timeline']=[]
        self.t['shots'][0]['camera']['movement']['type']='TRACK'
        cinematic=prepare(self.t)
        self.assertEqual('CINEMATIC',cinematic['presentation_mode'])
    def test_authored_complexity_cannot_bypass_routing(self):
        plan=prepare(self.t)
        plan['complexity']['motion']=999
        self.assert_issue(plan,'COMPLEXITY_DRIFT')
        plan['presentation_mode']='FAST'
        self.assert_issue(plan,'ROUTING_DRIFT')
    def test_malformed_decision_diagnostic_is_rejected(self):
        plan=prepare(self.t)
        del plan['decision_diagnostics'][0]['next_action']
        with self.assertRaises(ContractError):validate(plan)
    def test_sound_time_and_cause(self):
        self.t['audio_timeline']=[{'id':'sound_1','shot_id':'shot_001','layer':'effects','start_s':-1,'end_s':4,'cause':'magic'}]
        p=prepare(self.t);self.assert_issue(p,'AUDIO_TIME');self.assert_issue(p,'AUDIO_CAUSE')
    def test_json_duplicate_keys_and_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.json'
            for raw in ['{"id":1,"id":2}','{"x":NaN}']:
                path.write_text(raw)
                with self.assertRaises(ContractError):load(path)
    def test_new_revision_required_for_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'plan.json';save(p,{'id':1})
            with self.assertRaises(FileExistsError):save(p,{'id':2})
            self.assertEqual({'id':1},load(p))
    def test_cli_works_outside_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'plan.json'
            c=subprocess.run([sys.executable,str(SKILL/'scripts/vge.py'),'prepare',str(SKILL/'assets/templates/treatment.json'),'--output',str(p)],cwd=tmp,capture_output=True,text=True)
            self.assertEqual(0,c.returncode,c.stderr)
            c=subprocess.run([sys.executable,str(SKILL/'scripts/vge.py'),'validate',str(p)],cwd=tmp,capture_output=True,text=True)
            self.assertEqual('PASS',json.loads(c.stdout)['status'])


class ProfileTests(unittest.TestCase):
    def setUp(self):self.p=profile();self.s={'id':'shot_test','generation_mode':'T2V','duration_s':5,'parameters':{}}
    def test_supported_scoped_feature(self):self.assertEqual('SUPPORTED',negotiate(self.s,self.p)['status'])
    def test_each_unconfirmed_state_blocks(self):
        for state in ['UNKNOWN','PROPOSED','INFERRED','UNSUPPORTED','EXPIRED']:
            with self.subTest(state=state):
                if state in ('UNSUPPORTED', 'EXPIRED'):
                    self.p['status']=state
                else:
                    self.p['feature_evidence']['text_to_video']['status']=state
                self.assertEqual('BLOCKED',negotiate(self.s,self.p)['status'])
                self.p['status']='CONFIRMED'
                self.p['feature_evidence']['text_to_video']['status']='CONFIRMED'
    def test_optional_capability_can_only_degrade_explicitly(self):
        self.s['capability_requirements']=['reference_conditioning']
        self.s['degradable_capability_requirements']=['reference_conditioning']
        self.assertEqual('DEGRADED',negotiate(self.s,self.p)['status'])
    def test_feature_not_inherited_from_model_name(self):
        self.s['capability_requirements']=['audio_dialogue_lip_sync'];self.assertEqual('BLOCKED',negotiate(self.s,self.p)['status'])
    def test_expiry(self):
        self.p['validity']['expires_at']='2020-01-01T00:00:00Z';self.assertEqual('BLOCKED',negotiate(self.s,self.p)['status'])
    def test_continuous_minute_not_five_second_support(self):
        self.s['duration_s']=60;self.assertEqual('BLOCKED',negotiate(self.s,self.p)['status'])
    def test_frame_grid_valid_and_invalid(self):
        self.s['parameters']={'frame_count':121,'fps':24};self.assertEqual('SUPPORTED',negotiate(self.s,self.p)['status'])
        for value in [120,'bad',True,-1]:
            with self.subTest(value=value):
                self.s['parameters']['frame_count']=value;self.assertEqual('BLOCKED',negotiate(self.s,self.p)['status'])
    def test_invalid_resolution_and_fps(self):
        for pars in [{'width':999999,'height':-1,'fps':0},{'width':127},{'fps':100},{'seed':-1}]:
            with self.subTest(pars=pars):self.s['parameters']=pars;self.assertEqual('BLOCKED',negotiate(self.s,self.p)['status'])
    def test_candidates_are_non_executable(self):
        for path in (SKILL/'profiles').glob('*candidate.json'):
            self.assertEqual('BLOCKED',negotiate(self.s,load(path))['status'])


if __name__=='__main__':unittest.main()
