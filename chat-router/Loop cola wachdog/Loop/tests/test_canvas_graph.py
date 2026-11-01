"""Offline tests for graph pure backend; NOT live Harness/HTTP verification."""
import asyncio
import copy
import sys
import unittest
from pathlib import Path

# Allow 'nct_loop' package import when running from test folder, without installing.
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from nct_loop.canvas_graph import CanvasGraphError, validate_graph, from_loop_dag
from nct_loop.canvas_bridge import handle_canvas

BASE={"schema_id":"yaiwes.canvas.graph.v1","graph_id":"g1","project_id":"p1","mode":"dag",
      "nodes":[{"id":"a","title":"Primero","x":0,"y":0},{"id":"b","title":"Segundo","x":240,"y":0}],
      "edges":[{"id":"ab","source":"a","target":"b"}]}

class CanvasTests(unittest.TestCase):
 def test_valid(self):
  x=validate_graph(copy.deepcopy(BASE))
  self.assertTrue(x['ok']);self.assertEqual(x['stats']['nodes'],2)
 def test_stable_sha(self):
  self.assertEqual(validate_graph(BASE)['sha256'],validate_graph(copy.deepcopy(BASE))['sha256'])
 def test_dag_cycle_rejected(self):
  x=copy.deepcopy(BASE);x['edges'].append({'id':'ba','source':'b','target':'a'})
  with self.assertRaises(CanvasGraphError):validate_graph(x)
 def test_missing_node_rejected(self):
  x=copy.deepcopy(BASE);x['edges'][0]['source']='missing'
  with self.assertRaises(CanvasGraphError):validate_graph(x)
 def test_pass_no_evidence_rejected(self):
  x=copy.deepcopy(BASE);x['nodes'][0]['status']='PASS'
  with self.assertRaises(CanvasGraphError):validate_graph(x)
 def test_from_dag_no_fake_pass(self):
  x=from_loop_dag({'project_id':'p1','graph_id':'g1', 'dag_nodes':[
   {'node_id':'a','status':'PASS'},{'node_id':'b','depends_on':['a']} ]})
  self.assertEqual(x['graph']['nodes'][0]['status'],'UNKNOWN')
 def test_no_persistence(self):
  x=asyncio.run(handle_canvas('canvas_save',{'project_id':'p1','graph_id':'g1','graph':BASE,'expected_revision':0}))
  self.assertEqual(x['error'],'BACKEND_PERSISTENCE_MISSING')
 def test_persist_readback(self):
  mem={}
  async def load(scope,key):return mem.get((scope,key))
  async def save(scope,key,data):mem[(scope,key)]=data;return {'ok':True}
  x=asyncio.run(handle_canvas('canvas_save',{'project_id':'p1','graph_id':'g1','graph':BASE,'expected_revision':0},load_cb=load,save_cb=save))
  self.assertTrue(x['verified'])
  y=asyncio.run(handle_canvas('canvas_load',{'project_id':'p1','graph_id':'g1'},load_cb=load))
  self.assertEqual(x['sha256'],y['sha256'])
 def test_tampered_readback_rejected(self):
  mem={}
  def load(s,k):return mem.get((s,k))
  def save(s,k,d):
   wrong=copy.deepcopy(d)
   wrong['graph']['nodes'][0]['title']='TAMPERED'
   mem[(s,k)]=wrong
   return {'ok':True}
  x=asyncio.run(handle_canvas('canvas_save',{'project_id':'p1','graph_id':'g1','graph':BASE,'expected_revision':0},load_cb=load,save_cb=save))
  self.assertEqual(x['error'],'READBACK_MISMATCH')
 def test_corrupt_stored_hash_rejected(self):
  def load(s,k):return {'revision':1,'graph':BASE,'sha256':'wronghash'}
  x=asyncio.run(handle_canvas('canvas_load',{'project_id':'p1','graph_id':'g1'},load_cb=load))
  self.assertEqual(x['error'],'PERSISTED_HASH_MISMATCH')
 def test_revision_conflict(self):
  mem={}
  def load(s,k):return mem.get((s,k))
  def save(s,k,d):mem[(s,k)]=d;return {'ok':True}
  asyncio.run(handle_canvas('canvas_save',{'project_id':'p1','graph_id':'g1','graph':BASE,'expected_revision':0},load_cb=load,save_cb=save))
  x=asyncio.run(handle_canvas('canvas_save',{'project_id':'p1','graph_id':'g1','graph':BASE,'expected_revision':0},load_cb=load,save_cb=save))
  self.assertEqual(x['error'],'REVISION_CONFLICT')
 def test_validate_action(self):
  x=asyncio.run(handle_canvas('canvas_validate',{'graph':BASE}))
  self.assertTrue(x['ok'])
 def test_unknown_action(self):
  x=asyncio.run(handle_canvas('shell',{'graph':BASE}))
  self.assertEqual(x['error'],'UNKNOWN_ACTION')

if __name__=='__main__':unittest.main(verbosity=2)
