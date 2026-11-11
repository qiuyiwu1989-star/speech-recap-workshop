import importlib.util,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('recap_adapter',Path(__file__).resolve().parents[1]/'integrations/center/recap_adapter.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CenterTest(unittest.TestCase):
 def test_identity_retries_conflicts_evidence(self):
  with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'RECAP_CENTER_DATA':tmp,'RECAP_CENTER_OWNER':'fixture','MCP_CENTER_OWNER':'fixture'}):
   adapter=m.RecapAdapter();who={'owner_id':'fixture','credential_id':'fixture-key','actions':['read','create','revise']}
   def call(n,a,w=None):return adapter.call(n,a,w or who)['result']
   def data(r):self.assertFalse(r.get('isError'));return json.loads(r['content'][0]['text'])['data']
   args={'title':'虚构','transcript':'原文','request_id':'r1'}
   first=data(call('recap_create',args));self.assertEqual(first,data(call('recap_create',args)))
   self.assertTrue(call('recap_create',{**args,'title':'不同'})['isError'])
   self.assertTrue(call('recap_read',{'id':first['id']},{**who,'owner_id':'other'})['isError'])
   self.assertTrue(call('recap_create',args,{**who,'actions':['read']})['isError'])
   edit={'id':first['id'],'body':'正文','request_id':'r2','expected_revision':0}
   self.assertEqual(data(call('recap_revise',edit))['revision'],1)
   self.assertTrue(call('recap_revise',{**edit,'request_id':'r3'})['isError'])
   ev={'id':first['id'],'request_id':'r4','expected_revision':1,'units':[{'claim':'观点','source':'L2','target':'正文','status':'完整保留'}]}
   self.assertTrue(call('recap_evidence',ev)['isError'])
   ev['units'][0]['source']='L1';self.assertEqual(data(call('recap_evidence',ev))['revision'],2)
   data(call('recap_revise',{**edit,'expected_revision':2,'request_id':'r5'}))
   self.assertEqual(data(call('recap_read',{'id':first['id']}))['units'][0]['status'],'待核')
