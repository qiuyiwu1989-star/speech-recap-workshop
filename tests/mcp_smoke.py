"""Real stdio protocol smoke test; no model or network calls."""
import asyncio,json,os,sys,tempfile
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    with tempfile.TemporaryDirectory() as tmp:
        params=StdioServerParameters(command=sys.executable,args=[str(Path(__file__).resolve().parents[1]/'mcp_server.py')],env={**os.environ,'RECAP_DATA_DIR':tmp})
        async with stdio_client(params) as (reader,writer):
            async with ClientSession(reader,writer) as client:
                await client.initialize()
                tools=await client.list_tools()
                assert len(tools.tools)==8
                async def call(name,args={}):
                    r=await client.call_tool(name,args)
                    assert not r.isError,(name,r)
                    return json.loads(r.content[0].text)
                assert (await call('workshop_method'))['version']=='0.2.0'
                d=await call('workshop_create',{'title':'虚构测试','transcript':'原始观点\n\n案例限定条件'})
                id=d['id']
                r=await call('workshop_read',{'id':id,'start_line':3,'line_count':1})
                assert r['sources']==[{'id':'L3','text':'案例限定条件'}]
                await call('workshop_save_body',{'id':id,'body':'案例限定条件'})
                await call('workshop_save_evidence',{'id':id,'units':[{'claim':'限定条件','source':'L3','target':'案例限定条件','status':'完整保留'}]})
                r=await call('workshop_review_package',{'id':id})
                assert r['status']=='待人工审阅' and r['coverage']['完整保留']==1
                await call('workshop_save_body',{'id':id,'body':'新正文'})
                r=await call('workshop_read',{'id':id})
                assert r['coverage']['待核']==1 and not r['reviewed']
                v=await call('workshop_version',{'id':id,'version':r['versions'][0]['version']})
                assert v['body']=='案例限定条件'
                bad=await client.call_tool('workshop_read',{'id':'../bad'})
                assert bad.isError
                resources=await client.list_resources();assert resources.resources
                print('PASS: initialize, 8 tools, method resource, create, paged sources, evidence, body history, invalidation, review package, invalid ID')

asyncio.run(main())
