import tempfile
import unittest
from unittest.mock import patch
from workshop import create_app, flags, generate

class WorkshopTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.client = create_app(self.tmp.name).test_client()
    def tearDown(self):
        self.tmp.cleanup()
    def post(self,path,b):
        return self.client.post('/api/drafts'+path,json=b,headers={'X-Recap-Request':'1'})
    def test_lifecycle_and_human_protection(self):
        id=self.post('',{'title':'虚构工作坊','transcript':'今天我们讨论如何整理读书会记录。'}).json['id']
        self.assertEqual(self.client.get('/api/drafts/'+id+'/export/md').status_code,409)
        self.post('/'+id+'/save',{'body':'我的人工正文','reviewed':True})
        r=self.post('/'+id+'/generate',{'live':False})
        self.assertEqual(r.json['body'],'我的人工正文')
        self.assertEqual(r.json['reviewed'],0)
        self.post('/'+id+'/save',{'body':'## 标题\n\n<script>alert(1)</script>正文','reviewed':True})
        r=self.client.get('/api/drafts/'+id+'/export/html')
        self.assertEqual(r.status_code,200)
        self.assertNotIn(b'<script>',r.data)
        self.assertIn(b'<h2>',r.data)
        self.assertEqual(self.client.get('/api/drafts/'+id+'/export/md').status_code,200)
    def test_request_guards(self):
        self.assertEqual(self.client.post('/api/drafts',json={}).status_code,403)
        self.assertEqual(self.client.get('/',headers={'Host':'evil.example'}).status_code,403)
        self.assertEqual(self.post('',{'title':[], 'transcript':1}).status_code,400)
        self.assertEqual(self.client.get('/api/drafts/missing').status_code,404)
    def test_model_error_preserves_body(self):
        id=self.post('',{'title':'示例','transcript':'虚构文本'}).json['id']
        self.post('/'+id+'/save',{'body':'已保存','reviewed':True})
        with patch('workshop.generate',side_effect=RuntimeError('secret')):
            r=self.post('/'+id+'/generate',{'live':True})
        self.assertEqual(r.status_code,502)
        self.assertNotIn(b'secret',r.data)
        self.assertEqual(self.client.get('/api/drafts/'+id).json['body'],'已保存')
    def test_offline_and_flags(self):
        self.assertIn('离线演示',generate('虚构原文','标题'))
        self.assertTrue(flags('示例邮箱：demo@example.com'))

if __name__=='__main__':unittest.main()
