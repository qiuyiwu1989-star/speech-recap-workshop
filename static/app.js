const $=id=>document.getElementById(id);let current=null;
async function api(path,data){const r=await fetch('/api/drafts'+path,data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-Recap-Request':'1'},body:JSON.stringify(data)});const b=await r.json();if(!r.ok)throw Error(b.error||'请求失败');return b;}
async function run(fn){try{$('status').textContent='处理中…';await fn();$('status').textContent='已完成';}catch(e){$('status').textContent=e.message;}}
async function list(){const items=await api('');$('list').replaceChildren();for(const item of items){const b=document.createElement('button');b.textContent=item.title;b.onclick=()=>run(async()=>{if(current&&!confirm('切换会丢弃未保存的编辑，继续？'))return;show(await api('/'+item.id));});$('list').append(b);}}
function show(d){current=d;$('create').hidden=true;$('editor').hidden=false;$('heading').textContent=d.title;$('source').textContent=d.transcript;$('engine').textContent=d.engine;$('body').value=d.body;$('reviewed').checked=!!d.reviewed;$('flags').replaceChildren();for(const f of d.flags){const li=document.createElement('li');li.textContent=`${f.kind}：字符 ${f.start+1}–${f.end}`;$('flags').append(li);}for(const fmt of ['md','html'])$(fmt).href='/api/drafts/'+d.id+'/export/'+fmt;}
$('file').onchange=()=>run(async()=>{$('transcript').value=await $('file').files[0].text();});
$('new').onclick=()=>{if(current&&!confirm('新建会离开当前编辑，请确认已保存。'))return;current=null;$('create').hidden=false;$('editor').hidden=true;};
$('add').onclick=()=>run(async()=>{const d=await api('',{title:$('title').value,transcript:$('transcript').value});show(await api('/'+d.id));await list();});
for(const mode of ['demo','live'])$(mode).onclick=()=>run(async()=>{if(!confirm(mode==='live'?'将原始逐字稿发送至配置的模型服务，并可能产生费用。继续？':'生成离线演示？'))return;await api('/'+current.id+'/save',{body:$('body').value,reviewed:false});$('demo').disabled=$('live').disabled=true;try{show(await api('/'+current.id+'/generate',{live:mode==='live'}));}finally{$('demo').disabled=$('live').disabled=false;}});
$('adopt').onclick=()=>{if($('body').value&&!confirm('覆盖当前编辑区？保存前仍可重新打开已保存正文。'))return;$('body').value=current.engine;$('reviewed').checked=false;};
$('body').oninput=()=>{$('reviewed').checked=false;};
$('save').onclick=()=>run(async()=>show(await api('/'+current.id+'/save',{body:$('body').value,reviewed:$('reviewed').checked})));
run(list);
