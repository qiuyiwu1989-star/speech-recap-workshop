"""Local stdio MCP. Agent supplies reasoning; tools never call a model."""
import hashlib
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from workshop import create_app

ROOT = Path(__file__).resolve().parent
METHOD = ROOT / 'skills/speech-record-workshop/SKILL.md'
mcp = FastMCP('speech-recap-workshop')
_app = None


def api(path='', data=None):
    global _app
    if _app is None:
        _app = create_app()
    with _app.test_client() as client:
        r = client.get('/api/drafts'+path) if data is None else client.post('/api/drafts'+path,json=data,headers={'X-Recap-Request':'1'})
        if r.status_code >= 400:
            raise ValueError((r.get_json(silent=True) or {}).get('error',f'HTTP {r.status_code}'))
        return r.get_json()


def safe_id(id):
    if len(id)!=32 or any(c not in '0123456789abcdef' for c in id):
        raise ValueError('Invalid draft ID')
    return id


@mcp.tool()
def workshop_method() -> dict:
    """Read the versioned workflow before processing a speech. No model calls."""
    text=METHOD.read_text()
    return {'version':'0.2.0','sha256':hashlib.sha256(text.encode()).hexdigest(),'instructions':text}


@mcp.tool()
def workshop_list() -> list:
    """List local drafts; does not return transcript contents."""
    return api()


@mcp.tool()
def workshop_create(title: str, transcript: str) -> dict:
    """Preserve the supplied original transcript in local storage. Never publishes."""
    return api('',{'title':title,'transcript':transcript})


@mcp.tool()
def workshop_read(id: str, start_line: int=1, line_count: int=100) -> dict:
    """Read bounded original source lines plus current body, evidence and versions."""
    if start_line<1 or not 1<=line_count<=300:
        raise ValueError('start_line >= 1; line_count 1..300')
    d=api('/'+safe_id(id))
    d.pop('transcript')
    d['source_total_lines']=max((int(s['id'][1:]) for s in d['sources']),default=0)
    d['sources']=[s for s in d['sources'] if start_line<=int(s['id'][1:])<start_line+line_count]
    return d


@mcp.tool()
def workshop_save_body(id: str, body: str) -> dict:
    """Save Agent-authored Markdown as UNREVIEWED; prior body becomes a version.
    Do not overwrite a human's edits without reading and incorporating them first.
    """
    d=api('/'+safe_id(id)+'/save',{'body':body,'reviewed':False})
    return {'id':id,'reviewed':d['reviewed'],'versions':d['versions'],'coverage':d['coverage']}


@mcp.tool()
def workshop_save_evidence(id: str, units: list[dict]) -> dict:
    """Save information units: claim, source (L1...), target (exact body quote),
    status (待核/完整保留/部分保留/遗漏); optional note for omission reasons.
    Source existence and retained quotes are checked, semantic truth is not.
    """
    d=api('/'+safe_id(id)+'/review',{'units':units})
    return {'coverage':d['coverage'],'reviewed':d['reviewed'],'scope':'Only enumerated units; not full-source coverage'}


@mcp.tool()
def workshop_version(id: str, version: int) -> dict:
    """Read historical body and diff against current body; never restores implicitly."""
    if version<1: raise ValueError('version must be positive')
    return api('/'+safe_id(id)+'/versions/'+str(version))


@mcp.tool()
def workshop_review_package(id: str) -> dict:
    """Return an INTERNAL review package, not a published or human-approved artifact.
    Contains potentially private source evidence; do not upload to a public site.
    """
    d=api('/'+safe_id(id));method=workshop_method()
    return {'status':'待人工审阅','title':d['title'],'markdown':d['body'],
            'evidence':d['units'],'coverage':d['coverage'],'privacy_flags':d['flags'],
            'method_version':method['version'],'method_sha256':method['sha256'],
            'limitation':'Method fingerprint is the currently installed method, not proof it was followed.'}


@mcp.resource('workshop://method')
def method_resource() -> str:
    return METHOD.read_text()

if __name__=='__main__':
    mcp.run(transport='stdio')
