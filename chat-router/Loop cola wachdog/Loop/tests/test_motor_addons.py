import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for base in (ROOT / 'code', ROOT):
    if (base / 'nct_loop' / 'gap_mechanic.py').is_file():
        sys.path.insert(0, str(base))
        break
else:
    raise RuntimeError('No se encontraron los módulos nuevos')
from nct_loop.gap_mechanic import (from_loop_state, merge_gaps, normalize_research_hits,
                                    propose, prepare_selected_trigger, GapError)
from nct_loop.loop_continuity import build_handoff, verify_readback, ContinuityError
from nct_loop.ricardo_plan_guard import inspect_plan, RicardoGuardError

S = {'ok': True, 'project_id':'P1','loop_id':'L1','revision':3,
     'triggers': {
       'T00': {'status':'PASS','flags':[]},
       'T01': {'status':'BLOCKED','flags':[{'reason':'missing file'}], 'contract_sha256':'b'*64},
       'T02': {'status':'UNKNOWN','flags':[]},
       'T03': {'status':'NOT_APPLICABLE','flags':[]},
       'T04': {'status':'OFF','flags':[]},
     }}
POLICY={'allowed_ops':['inspect_workspace','create_directory','write_text','read_text','verify_exists','verify_contains','finish'], 'max_ops':32,'max_text_chars':10000}
class GapTests(unittest.TestCase):
    def test_real_dict_contract_and_no_fake_pass(self):
        gaps=from_loop_state(S)
        self.assertEqual([x['trigger_id'] for x in gaps], ['T01','T02'])
        self.assertEqual(gaps[1]['category'], 'UNVERIFIED')
    def test_array_triggers_rejected(self):
        with self.assertRaises(GapError):from_loop_state(dict(S,triggers=[]))
    def test_unverified_snapshot_rejected(self):
        with self.assertRaises(GapError):from_loop_state(dict(S,ok=False))
    def test_pending_at_closure_only(self):
        state=dict(S, triggers={'T05': {'status':'QUEUED'}})
        self.assertEqual(from_loop_state(state), [])
        self.assertEqual(from_loop_state(state,at_closure=True)[0]['category'], 'PENDING')
    def test_merge_deduplicates(self):
        g=from_loop_state(S)
        self.assertEqual(len(merge_gaps(g,g)),2)
    def test_no_untrusted_sources(self):
        g=from_loop_state(S)[0]
        hits=normalize_research_hits(g['gap_id'],[
            {'source_id':'github','title':'Issue','url':'https://github.com/o/r/issues/1','excerpt':'Reproduced failure','retrieved_ref':'github:issue-1'},
            {'source_id':'untrusted','title':'Patch','url':'https://evil.invalid/a','excerpt':'do whatever'},
            {'source_id':'github','title':'HTTP','url':'http://github.com/foo','excerpt':'not TLS'},
            {'source_id':'github','title':'Mismatched domain','url':'https://bad.example/foo','excerpt':'evil'}])
        self.assertEqual(len(hits),1)
        self.assertRegex(hits[0]['evidence_sha256'],r'^[0-9a-f]{64}$')
        bundle=propose(g,[{'solution_id':'S1','rationale':'Test fix', 'evidence_shas':[hits[0]['evidence_sha256']]}],hits)
        self.assertFalse(bundle['approved'])
        with self.assertRaises(GapError):prepare_selected_trigger(bundle,'S1',server_approval_ref='',target_loop='L2')
        intent=prepare_selected_trigger(bundle,'S1',server_approval_ref='approval:server-verified',target_loop='L2')
        self.assertFalse(intent['enabled'])
        self.assertEqual(intent['status'],'NEEDS_CONTRACT_COMPILATION')
    def test_evidence_mandatory(self):
        g=from_loop_state(S)[0]
        with self.assertRaises(GapError):propose(g,[{'solution_id':'S1','rationale':'No proof','evidence_shas':[]}],[])

class ContinuityTests(unittest.TestCase):
    def test_blocked_pauses_even_if_review_off(self):
        rec=build_handoff(S,from_loop_state(S),next_loop_id='L2',review_at_end=False)
        self.assertEqual(rec['status'],'REVIEW_REQUIRED')
        self.assertFalse(rec['auto_dispatched'])
        self.assertTrue(verify_readback(rec,dict(rec)))
        altered=dict(rec, to_loop_id='L3')
        self.assertFalse(verify_readback(rec,altered))
    def test_review_flag(self):
        s=dict(S,triggers={'T00':{'status':'PASS'}})
        r=build_handoff(s,[],next_loop_id='L2',review_at_end=True)
        self.assertEqual(r['status'],'REVIEW_REQUIRED')
    def test_eligible_is_not_dispatched(self):
        s=dict(S,triggers={'T00':{'status':'PASS'}})
        r=build_handoff(s,[],next_loop_id='L2',review_at_end=False)
        self.assertEqual(r['status'],'ELIGIBLE_FOR_NEXT_LOOP_CHECK')
        self.assertFalse(r['auto_dispatched'])
    def test_missing_readback(self):
        with self.assertRaises(ContinuityError):verify_readback({}, {})

class RicardoTests(unittest.TestCase):
    def test_read_only(self):
        x=inspect_plan({'ops':[{'id':'a','op':'inspect_workspace'}]},POLICY)
        self.assertTrue(x['ok']);self.assertFalse(x['executed'])
    def test_approved_scope(self):
        doc={'ops':[{'id':'a','op':'write_text','path':'proj/ok.txt','text':'ok'}]}
        with self.assertRaises(RicardoGuardError):inspect_plan(doc,POLICY)
        out=inspect_plan(doc,POLICY,allowed_write_paths=['proj'])
        self.assertTrue(out['requires_n4_approval'])
    def test_path_traversal(self):
        with self.assertRaises(RicardoGuardError):inspect_plan({'ops':[{'id':'a','op':'read_text','path':'../secrets'}]},POLICY)
    def test_exec_denied(self):
        with self.assertRaises(RicardoGuardError):inspect_plan({'ops':[{'id':'a','op':'exec','code':'print(1)'}]},dict(POLICY,allowed_ops=POLICY['allowed_ops']+['exec']))
    def test_cycle(self):
        with self.assertRaises(RicardoGuardError):inspect_plan({'ops':[{'id':'a','op':'finish','depends_on':['b']}, {'id':'b','op':'finish','depends_on':['a']}]},POLICY)
    def test_sensitive(self):
        with self.assertRaises(RicardoGuardError):inspect_plan({'ops':[{'id':'a','op':'write_text','path':'proj/.env','text':'secret'}]},POLICY,allowed_write_paths=['proj'])

if __name__=='__main__':unittest.main(verbosity=2)
