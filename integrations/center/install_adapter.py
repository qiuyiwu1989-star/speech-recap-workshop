"""Apply bounded local integration; never deploys or changes credentials."""
import argparse,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('mcp_directory',type=Path);args=p.parse_args();root=args.mcp_directory
changes={
'extra_domains.py':('DOMAINS = {',"DOMAINS = {\n    'recap': {'name': '实录工坊', 'module': 'recap_adapter', 'class': 'RecapAdapter',\n              'actions': {'read', 'create', 'revise'}, 'owner_env': 'RECAP_CENTER_OWNER'},"),
'center.py':("candidates = [('memory'","candidates = [('recap', '实录工坊'), ('memory'"),
'http_server.py':('readOnlyHint=True, destructiveHint=False, openWorldHint=tool',"readOnlyHint=tool['action'] == 'read', destructiveHint=False, openWorldHint=tool")}
outputs={}
for name,(old,new) in changes.items():
 text=(root/name).read_text()
 if new in text:continue
 if text.count(old)!=1:raise SystemExit(f'Unexpected source in {name}; inspect current production version before merging')
 outputs[root/name]=text.replace(old,new)
for path,text in outputs.items():path.write_text(text)
shutil.copy2(Path(__file__).with_name('recap_adapter.py'),root/'recap_adapter.py')
print('Local adapter files prepared. No deployment or grant changes.')
