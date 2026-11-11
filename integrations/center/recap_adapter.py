"""Fixed local MCP Butler adapter; private owner-bound SQLite, no model/network calls."""
import hashlib
import json
import os
import sqlite3
import uuid
from pathlib import Path
from jsonschema import validate

STR={'type':'string','minLength':1,'maxLength':100000}
ID={'type':'string','pattern':'^[a-f0-9]{32}$'}
REQ={'type':'string','minLength':1,'maxLength':128}
REV={'type':'integer','minimum':0}
DEFS=[
 ('recap_list','read',{},[]),
 ('recap_read','read',{'id':ID},['id']),
 ('recap_create','create',{'title':{'type':'string','minLength':1,'maxLength':300},'transcript':STR,'request_id':REQ},['title','transcript','request_id']),
 ('recap_revise','revise',{'id':ID,'body':STR,'expected_revision':REV,'request_id':REQ},['id','body','expected_revision','request_id']),
 ('recap_evidence','revise',{'id':ID,'expected_revision':REV,'request_id':REQ,'units':{'type':'array','maxItems':1000,'items':{'type':'object','properties':{'claim':STR,'source':{'type':'string','pattern':'^L[1-9][0-9]*$'},'target':{'type':'string','maxLength':100000},'status':{'enum':['待核','完整保留','部分保留','遗漏']},'note':{'type':'string','maxLength':4000}},'required':['claim','source','target','status'],'additionalProperties':False}}},['id','expected_revision','request_id','units'])]
TOOL_ACTIONS={n:a for n,a,_,_ in DEFS}
TOOL_SPECS=[{'name':n,'description':'Private speech workshop '+n+'; returns unreviewed data, never publishes.', 'inputSchema':{'type':'object','properties':p,'required':r,'additionalProperties':False},'annotations':{'readOnlyHint':a=='read','destructiveHint':False,'openWorldHint':False}} for n,a,p,r in DEFS]
SCHEMAS={s['name']:s['inputSchema'] for s in TOOL_SPECS}


def configuration_status():
    root=Path(os.environ.get('RECAP_CENTER_DATA',''))
    return {'configured':bool(os.environ.get('RECAP_CENTER_DATA')) and root.is_absolute() and bool(os.environ.get('RECAP_CENTER_OWNER'))}


class RecapAdapter:
    def call(self,name,args,identity):
        try:
            owner=os.environ.get('RECAP_CENTER_OWNER','')
            if not configuration_status()['configured'] or not owner or owner!=os.environ.get('MCP_CENTER_OWNER') or identity.get('owner_id')!=owner or not identity.get('credential_id'):
                raise ValueError('Identity denied')
            if name not in SCHEMAS or TOOL_ACTIONS[name] not in identity.get('actions',[]) or 'read' not in identity.get('actions',[]):
                raise ValueError('Permission denied')
            validate(args,SCHEMAS[name])
            if len(json.dumps(args).encode())>1_000_000:raise ValueError('Input limit')
            root=Path(os.environ['RECAP_CENTER_DATA'])/hashlib.sha256(owner.encode()).hexdigest()
            root.mkdir(parents=True,exist_ok=True,mode=0o700)
            with sqlite3.connect(root/'recap.sqlite3',timeout=10) as db:
                db.row_factory=sqlite3.Row
                db.execute('CREATE TABLE IF NOT EXISTS drafts(id TEXT PRIMARY KEY,title TEXT,transcript TEXT,body TEXT,units TEXT,revision INTEGER)')
                db.execute('CREATE TABLE IF NOT EXISTS receipts(request_id TEXT PRIMARY KEY,digest TEXT,result TEXT)')
                db.execute('CREATE TABLE IF NOT EXISTS history(id TEXT,revision INTEGER,body TEXT,units TEXT,actor TEXT,PRIMARY KEY(id,revision))')
                db.execute('BEGIN IMMEDIATE')
                digest=hashlib.sha256(json.dumps([name,args],sort_keys=True).encode()).hexdigest()
                receipt=db.execute('SELECT * FROM receipts WHERE request_id=?',(args.get('request_id',''),)).fetchone()
                if receipt:
                    if receipt['digest']!=digest:raise ValueError('Idempotency conflict')
                    result=json.loads(receipt['result'])
                else:
                    result=self.run(db,name,args,identity['credential_id'])
                    if 'request_id' in args:
                        db.execute('INSERT INTO receipts VALUES(?,?,?)',(args['request_id'],digest,json.dumps(result)))
                encoded=json.dumps({'untrusted_data':True,'data':result},ensure_ascii=False)
                if len(encoded.encode())>2_000_000:raise ValueError('Result limit')
            response={'content':[{'type':'text','text':encoded}]}
        except Exception:
            response={'isError':True,'content':[{'type':'text','text':'Recap request rejected: check identity, permission, schema, revision and request_id. No partial write committed.'}]}
        return {'jsonrpc':'2.0','id':1,'result':response}

    def run(self,db,name,a,actor):
        if name=='recap_list':
            return {'items':[dict(r) for r in db.execute('SELECT id,title,revision FROM drafts ORDER BY rowid DESC LIMIT 100')],'limit':100}
        if name=='recap_create':
            id=uuid.uuid4().hex
            db.execute('INSERT INTO drafts VALUES(?,?,?,?,?,?)',(id,a['title'],a['transcript'],'','[]',0))
            return {'id':id,'revision':0,'status':'待人工审阅'}
        row=db.execute('SELECT * FROM drafts WHERE id=?',(a['id'],)).fetchone()
        if row is None:raise ValueError('Not found')
        d=dict(row)
        if name=='recap_read':
            d['units']=json.loads(d['units']);d['sources']=[{'id':f'L{i}','text':line} for i,line in enumerate(d.pop('transcript').splitlines(),1) if line.strip()]
            d['status']='待人工审阅';return d
        if d['revision']!=a['expected_revision']:raise ValueError('Revision conflict')
        units=json.loads(d['units'])
        if name=='recap_revise':
            body=a['body']
            for u in units:u['status']='待核'
        else:
            body=d['body'];units=a['units']
            sources={f'L{i}' for i,line in enumerate(d['transcript'].splitlines(),1) if line.strip()}
            for u in units:
                if u['source'] not in sources:raise ValueError('Source missing')
                if u['status'] in ['完整保留','部分保留'] and (not u['target'] or u['target'] not in body):raise ValueError('Quote missing')
                if u['status'] in ['部分保留','遗漏'] and not u.get('note','').strip():raise ValueError('Reason required')
        db.execute('INSERT INTO history VALUES(?,?,?,?,?)',(d['id'],d['revision'],d['body'],d['units'],actor))
        db.execute('UPDATE drafts SET body=?,units=?,revision=revision+1 WHERE id=?',(body,json.dumps(units,ensure_ascii=False),d['id']))
        return {'id':d['id'],'revision':d['revision']+1,'status':'待人工审阅'}
