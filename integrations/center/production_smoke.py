import os,json,time,secrets,uuid,hashlib,fcntl,tempfile,subprocess,sqlite3
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
pid=subprocess.check_output(['systemctl','show','livepage-mcp','-p','MainPID','--value'],text=True).strip()
env=dict(x.decode().split('=',1) for x in (Path('/proc')/pid/'environ').read_bytes().split(b'\0') if b'=' in x)
registry=Path(env.get('LIVEPAGE_MCP_CLIENTS',str(Path(env.get('MCP_CENTER_STATE','/opt/livepage/state/mcp'))/'clients.json')))
lock=Path(env.get('MCP_CENTER_STATE',str(registry.parent)))/'center.lock'
cid='recap-smoke-'+uuid.uuid4().hex;key=secrets.token_urlsafe(40);draft=None

def change(action):
 with lock.open('a') as f:
  fcntl.flock(f,fcntl.LOCK_EX);d=json.loads(registry.read_text());st=registry.stat()
  if action=='add':d['clients'].append(dict(client_id=cid,name='Temporary recap acceptance',owner_id=env['MCP_CENTER_OWNER'],token_sha256=hashlib.sha256(key.encode()).hexdigest(),expires_at=time.time()+300,revoked=False,grants={'recap':{'actions':['read','create','revise']},'vault':{'actions':['public.read','private.read']}}))
  elif action=='remove':d['clients']=[r for r in d['clients'] if r.get('client_id')!=cid]
  else:
   for r in d['clients']:
    if r.get('client_id')==cid:
     if action=='readonly':r['grants']['recap']['actions']=['read']
     else:r['revoked']=True
  fd,name=tempfile.mkstemp(dir=registry.parent)
  with os.fdopen(fd,'w') as out:
   os.fchmod(out.fileno(),st.st_mode&0o777);os.fchown(out.fileno(),st.st_uid,st.st_gid);json.dump(d,out);out.flush();os.fsync(out.fileno())
  os.replace(name,registry)
def rpc(method,params={},status=200):
 try:
  with urlopen(Request('https://qiuyiwu.com/mcp',data=json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params)).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','Accept':'application/json, text/event-stream'}),timeout=30) as r:
   assert r.status==status;return json.load(r)['result']
 except HTTPError as e:
  assert e.code==status;return {}
def call(name,args):return rpc('tools/call',{'name':name,'arguments':args})
try:
 change('add');rpc('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'recap-smoke','version':'1'}})
 names={t['name'] for t in rpc('tools/list')['tools']};assert {'recap_create','recap_read','vault_ontology_read','vault_archive_rules'}<=names
 args={'title':'Synthetic acceptance','transcript':'Synthetic source only','request_id':cid+'-create'}
 r=call('recap_create',args);assert not r.get('isError'),r
 first=json.loads(r['content'][0]['text'])['data'];draft=first['id']
 second=json.loads(call('recap_create',args)['content'][0]['text'])['data'];assert first==second
 edit={'id':draft,'body':'Synthetic source only','expected_revision':0,'request_id':cid+'-edit'}
 assert not call('recap_revise',edit).get('isError')
 assert call('recap_revise',{**edit,'request_id':cid+'-stale'}).get('isError')
 assert not call('vault_archive_rules',{}).get('isError')
 change('readonly');assert 'recap_create' not in {t['name'] for t in rpc('tools/list')['tools']};assert call('recap_create',args).get('isError')
 change('revoke');rpc('tools/list',status=401)
 print('PASS public MCP: discovery, same-key archive compatibility, create, idempotency, revision conflict, grant withdrawal, revocation')
finally:
 change('remove')
 dbpath=Path(env['RECAP_CENTER_DATA'])/hashlib.sha256(env['MCP_CENTER_OWNER'].encode()).hexdigest()/'recap.sqlite3'
 if dbpath.exists():
  with sqlite3.connect(dbpath) as db:
   if draft:
    db.execute('DELETE FROM history WHERE id=?',(draft,));db.execute('DELETE FROM drafts WHERE id=?',(draft,))
   db.execute('DELETE FROM receipts WHERE request_id LIKE ?',(cid+'%',))
 print('Temporary key and synthetic data cleaned')
