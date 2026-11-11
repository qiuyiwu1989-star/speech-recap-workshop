import unittest
import test_workshop

class EvidenceTest(unittest.TestCase):
    setUp = test_workshop.WorkshopTest.setUp
    tearDown = test_workshop.WorkshopTest.tearDown
    post = test_workshop.WorkshopTest.post
    def test_sources_versions_and_invalidation(self):
        id=self.post('',{'title':'来源测试','transcript':'第一条原话\n\n第二条原话'}).json['id']
        self.post('/'+id+'/save',{'body':'保留原句','reviewed':False})
        unit={'claim':'重要观点','source':'L3','target':'保留原句','status':'完整保留'}
        r=self.post('/'+id+'/review',{'units':[unit]})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['coverage']['完整保留'],1)
        self.assertEqual(r.json['sources'][1]['id'],'L3')
        unit['source']='L99'
        self.assertEqual(self.post('/'+id+'/review',{'units':[unit]}).status_code,400)
        r=self.post('/'+id+'/save',{'body':'修改后正文','reviewed':False})
        self.assertEqual(r.json['units'][0]['status'],'待核')
        version=r.json['versions'][0]['version']
        r=self.client.get('/api/drafts/'+id+'/versions/'+str(version))
        self.assertEqual(r.json['body'],'保留原句')
        self.assertIn('修改后正文',r.json['diff'])

    def test_pending_units_block_approval(self):
        id=self.post('',{'title':'复核','transcript':'原文'}).json['id']
        self.post('/'+id+'/save',{'body':'正文','reviewed':False})
        self.post('/'+id+'/review',{'units':[{'claim':'观点','source':'L1','target':'','status':'待核'}]})
        r=self.post('/'+id+'/save',{'body':'正文','reviewed':True})
        self.assertFalse(r.json['reviewed'])
        self.assertEqual(self.client.get('/api/drafts/'+id+'/export/md').status_code,409)
