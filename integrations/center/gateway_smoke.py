import asyncio,json,os,tempfile
from mcp import types
from http_server import create_gateway,current_identity,current_grants
async def main():
 with tempfile.TemporaryDirectory() as tmp:
  os.environ.update(RECAP_CENTER_DATA=tmp,RECAP_CENTER_OWNER='fixture',MCP_CENTER_OWNER='fixture')
  g=create_gateway();a=current_identity.set({'client_id':'test','owner_id':'fixture'});b=current_grants.set({'recap':{'actions':['read','create','revise']}})
  try:
   listing=await g._mcp_server.request_handlers[types.ListToolsRequest](types.ListToolsRequest(method='tools/list'))
   tools={t.name:t for t in listing.root.tools};assert 'recap_create' in tools and not tools['recap_create'].annotations.readOnlyHint
   req=types.CallToolRequest(method='tools/call',params=types.CallToolRequestParams(name='recap_create',arguments={'title':'fixture','transcript':'synthetic source','request_id':'test'}))
   r=await g._mcp_server.request_handlers[types.CallToolRequest](req);assert not r.root.isError,r
   current_grants.set({'recap':{'actions':['read']}})
   r=await g._mcp_server.request_handlers[types.CallToolRequest](req);assert r.root.isError
   print('PASS center SDK discovery, write annotation, create dispatch, immediate permission withdrawal')
  finally:current_identity.reset(a);current_grants.reset(b)
asyncio.run(main())
