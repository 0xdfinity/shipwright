"""Small local web interface for streaming Shipwright runs."""
from __future__ import annotations

import difflib
import json
import os
import queue
import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from .agent import DEFAULT_MODEL, Event, make_client, run_agent
from .sandbox import Sandbox

app = FastAPI(title="Shipwright")


class RunRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=2000)
    project: str = Field(min_length=1, max_length=500)


class RecordingSandbox(Sandbox):
    """Keep full results for the browser while delegating all behavior to Sandbox."""
    last_result: dict

    def __init__(self, root: str | Path):
        super().__init__(root)
        self.last_result = {}

    def list_files(self, max_files: int = 300) -> list[str]:
        result = super().list_files(max_files)
        self.last_result = {"files": result}
        return result

    def read_file(self, rel: str, max_chars: int = 20000) -> str:
        result = super().read_file(rel, max_chars)
        self.last_result = {"path": rel, "content": result}
        return result

    def write_file(self, rel: str, content: str) -> str:
        p = self.resolve(rel)
        old = p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""
        result = super().write_file(rel, content)
        self.last_result = {
            "path": rel,
            "diff": "".join(difflib.unified_diff(old.splitlines(keepends=True), content.splitlines(keepends=True), fromfile=f"a/{rel}", tofile=f"b/{rel}")),
            "content": content,
            "result": result,
        }
        return result

    def run_tests(self) -> dict:
        result = super().run_tests()
        self.last_result = result
        return result


def _emit(q: queue.Queue, event: dict) -> None:
    q.put(event)


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML


@app.post("/api/runs")
def start_run(request: RunRequest):
    goal = request.goal.strip()
    if not goal:
        raise HTTPException(400, "goal is required")
    workspace = Path(os.environ.get("SHIPWRIGHT_WORKSPACE", Path.cwd())).resolve()
    project = (workspace / request.project).resolve()
    if project != workspace and workspace not in project.parents:
        raise HTTPException(400, "project must be inside the Shipwright workspace")
    if not project.is_dir():
        raise HTTPException(404, "project directory not found inside the Shipwright workspace")
    events: queue.Queue = queue.Queue()
    run_id = f"{time.time_ns()}"

    def worker():
        sandbox = RecordingSandbox(project)
        started = time.monotonic()
        _emit(events, {"kind": "start", "data": {"run_id": run_id, "model": DEFAULT_MODEL, "project": str(project.relative_to(workspace))}})

        def on_event(event: Event):
            data = dict(event.data)
            if event.kind == "tool":
                data["result"] = sandbox.last_result
            _emit(events, {"kind": event.kind, "data": data})

        try:
            result = run_agent(goal, sandbox, make_client(), model=DEFAULT_MODEL, on_event=on_event)
            _emit(events, {"kind": "complete", "data": {**result, "elapsed_seconds": round(time.monotonic() - started, 2)}})
        except Exception as exc:
            _emit(events, {"kind": "error", "data": {"message": str(exc)}})
        finally:
            events.put(None)

    threading.Thread(target=worker, daemon=True).start()

    def stream():
        while True:
            try:
                event = events.get(timeout=15)
            except queue.Empty:
                yield ": keep-alive\n\n"
                continue
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Shipwright</title>
<style>
:root{color-scheme:dark;--bg:#080b12;--panel:rgba(17,23,36,.78);--line:rgba(152,177,214,.15);--muted:#8996ad;--text:#e7edf8;--cyan:#73e0d0;--red:#ff667e;--green:#73e0a1}*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 50% -18%,#1a3150 0%,transparent 54%),var(--bg);color:var(--text);font:14px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;min-height:100vh}.wrap{max-width:1020px;margin:auto;padding:54px 24px 80px}.top{display:flex;align-items:center;gap:12px;margin-bottom:36px}.mark{width:34px;height:34px;border:1px solid #73e0d077;border-radius:11px;display:grid;place-items:center;color:var(--cyan);box-shadow:0 0 28px #73e0d022}.brand{font:600 15px/1.1 ui-sans-serif,system-ui;letter-spacing:.08em}.label{color:var(--muted);font-size:11px;letter-spacing:.16em;text-transform:uppercase}.hero{margin-bottom:26px}.hero h1{font:500 clamp(28px,4vw,44px)/1.1 ui-sans-serif,system-ui;letter-spacing:-.04em;margin:10px 0}.hero p{color:var(--muted);margin:0}.glass{background:linear-gradient(140deg,rgba(26,36,54,.82),rgba(12,17,27,.86));border:1px solid var(--line);border-radius:20px;box-shadow:0 24px 80px #0007,inset 0 1px #ffffff0a;backdrop-filter:blur(18px)}.form{padding:20px;margin-bottom:20px}.row{display:flex;gap:12px;align-items:end}.field{flex:1}.field label{display:block;color:var(--muted);font-size:11px;margin:0 0 8px 2px}input,textarea{width:100%;border:1px solid var(--line);border-radius:12px;background:#080d17;color:var(--text);padding:13px 14px;font:13px ui-monospace,monospace;outline:none}textarea{height:78px;resize:vertical}input:focus,textarea:focus{border-color:#73e0d088}.goal{margin-bottom:14px}button{height:45px;border:0;border-radius:12px;padding:0 21px;color:#07100f;background:linear-gradient(135deg,#a3f0dd,#66d8cd);font:700 12px ui-monospace,monospace;letter-spacing:.04em;cursor:pointer;white-space:nowrap}button:disabled{opacity:.45;cursor:wait}.stream{overflow:hidden}.streamhead{display:flex;justify-content:space-between;align-items:center;padding:17px 20px;border-bottom:1px solid var(--line)}.led{width:7px;height:7px;border-radius:50%;background:#667084;display:inline-block;margin-right:8px}.led.live{background:var(--cyan);box-shadow:0 0 12px var(--cyan);animation:pulse 1.4s infinite}.state{color:var(--muted);font-size:11px}.events{min-height:320px;max-height:62vh;overflow:auto;padding:12px 20px 20px}.empty{display:grid;min-height:280px;place-items:center;color:#58647a;text-align:center}.event{border-bottom:1px solid #ffffff0a;padding:13px 0}.eventtop{display:flex;justify-content:space-between;gap:12px;color:var(--muted);font-size:11px}.tool{color:var(--cyan);letter-spacing:.08em}.status{font-weight:700}.status.red{color:var(--red)}.status.green{color:var(--green)}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#060a11;border:1px solid #ffffff0b;border-radius:10px;padding:12px;margin:10px 0 0;color:#bdc9db;font:11px/1.6 ui-monospace,monospace;max-height:280px;overflow:auto}.diff .minus{color:#ff8293}.diff .plus{color:#82e8aa}.note{color:var(--muted);font-size:11px;margin:13px 3px 0}@keyframes pulse{50%{opacity:.35}}@media(max-width:680px){.wrap{padding:32px 15px}.row{align-items:stretch;flex-direction:column}button{width:100%}.hero{margin-bottom:20px}}
</style></head><body><main class="wrap"><header class="top"><div class="mark">S</div><div class="brand">SHIPWRIGHT</div><div class="label" style="margin-left:auto">agent console / local</div></header><section class="hero"><div class="label">repair loop / live</div><h1>Make the tests green.</h1><p>Watch the agent inspect, edit, and verify a Python project.</p></section><form class="glass form" id="form"><div class="field goal"><label for="goal">PLAIN-LANGUAGE GOAL</label><textarea id="goal" required placeholder="Fix the failing tests in the project"></textarea></div><div class="row"><div class="field"><label for="project">PROJECT PATH INSIDE WORKSPACE</label><input id="project" value="demo_project" required placeholder="demo_project"></div><button id="run">RUN AGENT</button></div></form><section class="glass stream"><div class="streamhead"><div><span class="led" id="led"></span><span class="label">event stream</span></div><div class="state" id="state">waiting for a run</div></div><div class="events" id="events"><div class="empty">Your agent's work will appear here.<br>Files, diffs, and test output. Live.</div></div></section><div class="note">Runs locally. The selected project must be inside the Shipwright workspace.</div></main>
<script>
const form=document.querySelector('#form'),button=document.querySelector('#run'),events=document.querySelector('#events'),state=document.querySelector('#state'),led=document.querySelector('#led');
function block(label,body,cls=''){const el=document.createElement('div');el.className='event '+cls;const top=document.createElement('div');top.className='eventtop';const l=document.createElement('span');l.className='tool';l.textContent=label;top.append(l);el.append(top);if(body!==undefined&&body!==null&&body!==''){const pre=document.createElement('pre');if(cls==='diff'){for(const line of body.split('\n')){const span=document.createElement('span');span.textContent=line+'\n';span.className=line.startsWith('+')&&!line.startsWith('+++')?'plus':line.startsWith('-')&&!line.startsWith('---')?'minus':'';pre.append(span)}}else pre.textContent=typeof body==='string'?body:JSON.stringify(body,null,2);el.append(pre)}events.append(el);events.scrollTop=events.scrollHeight}
form.addEventListener('submit',async e=>{e.preventDefault();button.disabled=true;events.innerHTML='';led.classList.add('live');state.textContent='connecting';try{const res=await fetch('/api/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({goal:document.querySelector('#goal').value,project:document.querySelector('#project').value})});if(!res.ok)throw new Error((await res.json()).detail||'could not start run');const reader=res.body.getReader(),decoder=new TextDecoder();let buffer='';state.textContent='running';while(true){const {value,done}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});let cut;while((cut=buffer.indexOf('\n\n'))>=0){const frame=buffer.slice(0,cut);buffer=buffer.slice(cut+2);const line=frame.split('\n').find(x=>x.startsWith('data: '));if(!line)continue;const ev=JSON.parse(line.slice(6)),d=ev.data||{};if(ev.kind==='start'){block('RUN STARTED',`model: ${d.model}\nproject: ${d.project}`)}else if(ev.kind==='tool'){let label=d.name.toUpperCase();const r=d.result||{};if(d.name==='list_files')block(label,(r.files||[]).join('\n'));else if(d.name==='read_file')block(label+' · '+(r.path||''),r.content||d.result_preview);else if(d.name==='write_file')block(label+' · '+(r.path||''),r.diff||r.content||d.result_preview,'diff');else if(d.name==='run_tests'){const passed=!!r.passed;block('TESTS '+(passed?'GREEN':'RED'),r.output||JSON.stringify(r), '');const tag=events.lastElementChild.querySelector('.tool');tag.className='tool status '+(passed?'green':'red')}}else if(ev.kind==='text')block('AGENT',d.content);else if(ev.kind==='done')block('AGENT '+String(d.status||'').toUpperCase(),d.summary||'');else if(ev.kind==='complete'){block('RUN COMPLETE · '+String(d.status||'').toUpperCase(),`steps: ${d.steps}\ntime: ${d.elapsed_seconds}s\n${d.summary||''}`);state.textContent=d.status==='passed'?'tests green':'run '+d.status;led.classList.remove('live')}else if(ev.kind==='error'){block('ERROR',d.message);state.textContent='run failed';led.classList.remove('live')}}}}catch(err){block('ERROR',err.message);state.textContent='could not run';led.classList.remove('live')}finally{button.disabled=false;led.classList.remove('live')}});
</script></body></html>'''
