import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_planning import treatment, profile
from test_evidence_runtime_media import evidence
from vge_core import ContractError, prepare, validate, repair_scope
from vge_evidence import validate_observation
from vge_provider import hailuo_request, hailuo_submit, hailuo_poll


class RepairAndBoundaryTests(unittest.TestCase):
    def test_repair_invalidates_only_descendants(self):
        plan={'shots':[{'id':'a','dependency_ids':[],'acceptance_ids':['QG-07']},{'id':'b','dependency_ids':['a'],'acceptance_ids':['QG-05']},{'id':'c','dependency_ids':[],'acceptance_ids':['QG-13']}]}
        original=copy.deepcopy(plan);result=repair_scope(plan,['a'])
        self.assertEqual(['a','b'],result['affected_shot_ids']);self.assertEqual(['c'],result['preserved_shot_ids']);self.assertEqual(original,plan)
    def test_timeline_and_contact_mutations(self):
        p=prepare(treatment());p['narrative_timeline'][0]['time']['start_s']=1
        self.assertIn('TIMELINE_INTERVAL',[i['id'] for i in validate(p)['issues']])
        p=prepare(treatment());p['contact_graphs'][0]['actor']='missing'
        self.assertIn('CONTACT_CAUSE',[i['id'] for i in validate(p)['issues']])
    def test_unresolved_prior_state_not_promoted(self):
        t=treatment();t['shots'][0]['state_changes'].append({'property':'vehicle_van.speed','prior':'UNKNOWN','next':'moving','cause':'pull'})
        self.assertIn('UNRESOLVED_PRECONDITION',[i['id'] for i in prepare(t)['validation']['issues']])
    def test_authored_assembly_wrong_keys_actionable(self):
        t=treatment();t['assembly_plan']={'shot_order':['shot_001']}
        with self.assertRaisesRegex(ContractError,'shot_ids'):prepare(t)
    def test_failed_or_submitted_attempt_cannot_support_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'data';p.write_bytes(b'test');e=evidence(p)
            for state in ['UNKNOWN','SUBMITTED','RUNNING','FAILED','CANCELLED']:
                with self.subTest(state=state):
                    e['attempt']['status']=state
                    with self.assertRaises(ContractError):validate_observation(e['observation'],e['artifact'],e['attempt'],e['shot'])


class ProviderTests(unittest.TestCase):
    def setUp(self):
        p=profile();p.update(provider='minimax_api',model='MiniMax-Hailuo-2.3')
        self.spec={'profile':p,'shot':{'id':'shot_external','generation_mode':'T2V','duration_s':6,'parameters':{}},'prompt':'A single unbranded paper boat drifts across a quiet pond.','resolution':'768P'}
    def test_offline_request_does_not_require_credentials(self):
        result=hailuo_request(self.spec);self.assertEqual('PLAN_ONLY',result['mode']);self.assertEqual(6,result['body']['duration'])
        self.assertFalse(result['body']['prompt_optimizer'])
    def test_no_silent_prompt_truncation(self):
        self.spec['prompt']='x'*2001
        with self.assertRaises(ContractError):hailuo_request(self.spec)
    def test_unsupported_duration_resolution(self):
        self.spec['resolution']='1080P';self.spec['shot']['duration_s']=10
        with self.assertRaises(ContractError):hailuo_request(self.spec)
    def test_paid_authorization_precedes_transport(self):
        with tempfile.TemporaryDirectory() as tmp,self.assertRaises(ContractError):hailuo_submit(self.spec,tmp)
    def test_image_transfer_requires_explicit_scope(self):
        self.spec['shot']['generation_mode']='I2V';self.spec['first_frame_image']='https://example.com/image.png'
        self.spec['profile']['supports']['modes'].append('I2V')
        self.spec['profile']['feature_evidence']['image_to_video']=self.spec['profile']['feature_evidence']['text_to_video']
        with tempfile.TemporaryDirectory() as tmp,self.assertRaisesRegex(ContractError,'transfer'):hailuo_submit(self.spec,tmp,True)
    def test_image_transfer_requires_explicit_consent_status(self):
        self.spec['shot']['generation_mode']='I2V';self.spec['first_frame_image']='https://example.com/image.png'
        self.spec['profile']['supports']['modes'].append('I2V')
        self.spec['profile']['feature_evidence']['image_to_video']=self.spec['profile']['feature_evidence']['text_to_video']
        self.spec['reference_provenance']={'rights_status':'CONFIRMED'}
        with tempfile.TemporaryDirectory() as tmp,self.assertRaisesRegex(ContractError,'consent'):hailuo_submit(self.spec,tmp,True,True)
    def test_submission_and_poll_with_fake_provider(self):
        class Fake:
            def __init__(self):self.posts=0
            def request(self,route,body=None):
                if body is not None:self.posts+=1;return {'base_resp':{'status_code':0},'task_id':'task_1'}
                return {'base_resp':{'status_code':0},'status':'Success','file_id':'file_1'}
        fake=Fake()
        with tempfile.TemporaryDirectory() as tmp:
            result=hailuo_submit(self.spec,tmp,True,client=fake)
            self.assertEqual('SUBMITTED',result['submission']['status']);self.assertEqual(1,fake.posts)
            self.assertEqual('SUCCEEDED',hailuo_poll('task_1',1,.01,fake)['status'])
            self.assertNotIn('Authorization',(Path(result['run_directory'])/'request.json').read_text())
    def test_uncertain_paid_submission_is_not_retried(self):
        class Fake:
            def __init__(self):self.posts=0
            def request(self,route,body=None):self.posts+=1;raise ContractError('connection lost')
        fake=Fake()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ContractError):hailuo_submit(self.spec,tmp,True,client=fake)
            self.assertEqual(1,fake.posts);self.assertEqual(1,len(list(Path(tmp).glob('*/submission-001.json'))))


if __name__=='__main__':unittest.main()
