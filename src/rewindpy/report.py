from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import prepare_report_payload, verify_report_integrity

_REPORT_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "report_title": "RewindPy crash report",
        "crash_slice": "Crash Slice",
        "all_events": "All Events",
        "source": "Source",
        "variables": "Variables",
        "call_stack": "Call stack",
        "exception_chain": "Exceptions",
        "caused_by": "Caused by",
        "during_handling": "While handling",
        "root_exception": "Root cause",
        "outer_exception": "Outer exception",
        "chain_truncated": "Exception chain was truncated for safety.",
        "chain_cycle": "A cycle was detected in the exception chain.",
        "exception_notes": "Notes",
        "no_exception_chain": "No exception chain captured",
        "changes": "Changes",
        "origin": "Likely origin",
        "no_origin": "No earlier value origin was identified.",
        "no_source": "Source unavailable",
        "no_variables": "No local variables captured",
        "no_changes": "No variable changes on this step",
        "play": "Play",
        "pause": "Pause",
        "previous": "Previous",
        "next": "Next",
        "open_source": "Open source",
        "copy_diagnostic": "Copy diagnostic",
        "copy_location": "Copy location",
        "copied": "Copied",
        "copy_failed": "Copy failed",
        "step": "Step",
        "of": "of",
        "events": "events",
        "retained": "retained",
        "discarded": "discarded",
        "compressed": "compressed",
        "trimmed": "trimmed",
        "files": "files",
        "trace_time": "trace time",
        "report_size": "report data",
        "repeat": "repeated",
        "times": "times",
        "jump_origin": "Jump to origin",
        "theme": "Theme",
        "speed": "Speed",
        "shortcuts": "←/J previous · →/K next · Space play · O open · C copy · L location",
        "timeline": "Execution timeline",
        "current_event": "Current event",
        "function": "Function",
        "location": "Location",
        "event": "Event",
        "depth": "Depth",
    },
    "zh": {
        "report_title": "RewindPy 崩溃报告",
        "crash_slice": "崩溃切片",
        "all_events": "全部事件",
        "source": "源代码",
        "variables": "变量",
        "call_stack": "调用栈",
        "exception_chain": "异常链",
        "caused_by": "由此异常导致",
        "during_handling": "处理以下异常时发生",
        "root_exception": "根本异常",
        "outer_exception": "最外层异常",
        "chain_truncated": "异常链过长，已为安全起见截断。",
        "chain_cycle": "检测到异常链循环引用。",
        "exception_notes": "备注",
        "no_exception_chain": "没有捕获到异常链",
        "changes": "变量变化",
        "origin": "可能来源",
        "no_origin": "没有找到可信的更早数值来源。",
        "no_source": "无法获取源代码",
        "no_variables": "没有捕获到局部变量",
        "no_changes": "这一步没有变量变化",
        "play": "播放",
        "pause": "暂停",
        "previous": "上一步",
        "next": "下一步",
        "open_source": "打开源码",
        "copy_diagnostic": "复制诊断",
        "copy_location": "复制位置",
        "copied": "已复制",
        "copy_failed": "复制失败",
        "step": "步骤",
        "of": "/",
        "events": "个事件",
        "retained": "已保留",
        "discarded": "已丢弃",
        "compressed": "已压缩",
        "trimmed": "已裁剪",
        "files": "个文件",
        "trace_time": "追踪耗时",
        "report_size": "报告数据",
        "repeat": "重复",
        "times": "次",
        "jump_origin": "跳转到来源",
        "theme": "主题",
        "speed": "速度",
        "shortcuts": "←/J 上一步 · →/K 下一步 · 空格播放 · O 打开 · C 复制 · L 位置",
        "timeline": "执行时间线",
        "current_event": "当前事件",
        "function": "函数",
        "location": "位置",
        "event": "事件",
        "depth": "深度",
    },
}

HTML_TEMPLATE = r'''<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>RewindPy</title>
<style>
:root{color-scheme:dark;--bg:#080a10;--panel:#0d111a;--panel2:#121824;--panel3:#182131;--border:#263247;--text:#eef2ff;--muted:#8e9bb0;--accent:#7c8cff;--accent2:#51d6c7;--danger:#fb7185;--warning:#fbbf24;--success:#86efac;--line:#1b2535;--shadow:0 20px 60px rgba(0,0,0,.35);--header:68px;--transport:116px}
html[data-theme="light"]{color-scheme:light;--bg:#f3f5f9;--panel:#fff;--panel2:#f8fafc;--panel3:#edf2f7;--border:#d8e0ec;--text:#152033;--muted:#66758c;--line:#edf1f6;--shadow:0 18px 48px rgba(31,41,55,.12)}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden}body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;background:radial-gradient(circle at 15% -20%,rgba(124,140,255,.16),transparent 35%),var(--bg);color:var(--text)}button,input,select{font:inherit}
.app-header{position:fixed;z-index:20;inset:0 0 auto;height:var(--header);display:flex;align-items:center;gap:14px;padding:0 18px;border-bottom:1px solid var(--border);background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(18px)}
.logo{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;background:linear-gradient(145deg,rgba(124,140,255,.28),rgba(81,214,199,.1));border:1px solid rgba(124,140,255,.38);font-weight:900}.brand{min-width:0;flex:1}.brand h1{font-size:15px;margin:0}.crash{font:12px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--danger);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:4px}.header-actions{display:flex;align-items:center;gap:7px}.btn,.seg button{height:36px;border:1px solid var(--border);border-radius:10px;background:var(--panel2);color:var(--muted);cursor:pointer;font-size:12px;font-weight:700;padding:0 11px}.btn:hover,.seg button:hover{color:var(--text);background:var(--panel3)}.btn.primary{color:white;background:linear-gradient(135deg,#6d7cff,#5264df);border-color:transparent}.btn.success{color:var(--success)}.seg{height:38px;border:1px solid var(--border);border-radius:11px;padding:3px;background:var(--panel);display:flex}.seg button{height:30px;border:0;background:transparent}.seg button.active{color:var(--text);background:var(--panel3)}#languageToggle{width:72px}.workspace{position:fixed;inset:var(--header) 0 var(--transport);display:grid;grid-template-columns:minmax(0,1.55fr) minmax(350px,.85fr);gap:10px;padding:10px;overflow:hidden}.panel{min-width:0;min-height:0;border:1px solid var(--border);border-radius:14px;background:color-mix(in srgb,var(--panel) 96%,transparent);box-shadow:var(--shadow);overflow:hidden}.panel-head{height:46px;display:flex;align-items:center;justify-content:space-between;padding:0 13px;border-bottom:1px solid var(--border);background:var(--panel2)}.panel-title{font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase}.file-name{max-width:65%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font:11px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted)}.code-scroll{height:calc(100% - 46px);overflow:auto;scrollbar-gutter:stable}.code-line{display:grid;grid-template-columns:34px 50px minmax(0,1fr);min-height:24px;font:13px/24px ui-monospace,SFMono-Regular,Consolas,monospace;border-left:3px solid transparent}.code-line:hover{background:rgba(124,140,255,.05)}.code-line.active{background:rgba(124,140,255,.14);border-left-color:var(--accent)}.code-line.crash-line{box-shadow:inset 0 0 0 1px rgba(251,113,133,.35)}.code-line.origin-line:not(.active){background:rgba(251,191,36,.08);border-left-color:var(--warning)}.arrow{text-align:center;color:transparent}.active .arrow{color:var(--accent2)}.line-no{text-align:right;padding-right:10px;color:#58667c;user-select:none}.code{white-space:pre;padding-right:20px}.kw{color:#c792ea}.str{color:#c3e88d}.num{color:#f78c6c}.com{color:#637777;font-style:italic}.fn{color:#82aaff}.right{display:grid;grid-template-rows:minmax(180px,.72fr) minmax(230px,1fr);gap:10px;min-height:0}.event-card{padding:14px;overflow:auto;height:calc(100% - 46px)}.event-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.metric{padding:10px;border:1px solid var(--border);border-radius:10px;background:var(--panel2)}.metric label{display:block;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.06em}.metric b{display:block;margin-top:5px;font:12px ui-monospace,SFMono-Regular,Consolas,monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.origin{margin-top:10px;padding:11px;border:1px solid rgba(251,191,36,.25);border-radius:11px;background:rgba(251,191,36,.07)}.origin h3{font-size:11px;margin:0 0 6px;color:var(--warning);text-transform:uppercase}.origin p{margin:0 0 9px;color:var(--muted);font-size:12px;line-height:1.55}.tabs{display:flex;gap:4px}.tab{height:30px;border:0;border-radius:8px;background:transparent;color:var(--muted);font-size:11px;font-weight:700;cursor:pointer;padding:0 9px}.tab.active{background:var(--panel3);color:var(--text)}.tab-body{height:calc(100% - 46px);overflow:auto;padding:10px}.variable{border-bottom:1px solid var(--line);padding:8px 6px}.variable:last-child{border-bottom:0}.var-top{display:flex;justify-content:space-between;gap:10px}.var-name{font:12px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--accent2)}.var-type{font-size:10px;color:var(--muted)}.var-value{margin-top:5px;font:12px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--text);white-space:pre-wrap;word-break:break-word}.variable.changed{background:rgba(124,140,255,.07);border-radius:8px}.change{padding:9px;border-bottom:1px solid var(--line);font:12px ui-monospace,SFMono-Regular,Consolas,monospace}.before{color:var(--danger)}.after{color:var(--success)}.frame{display:flex;align-items:center;gap:8px;padding:8px;border-bottom:1px solid var(--line);cursor:pointer}.frame:hover{background:var(--panel3)}.frame-depth{width:22px;color:var(--muted);font:10px monospace}.frame-main{min-width:0}.frame-fn{font:12px monospace;color:var(--accent2)}.frame-loc{font:10px monospace;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.exception-chain{display:grid;gap:0}.exception-node{width:100%;text-align:left;padding:11px;border:1px solid var(--border);border-radius:11px;background:var(--panel2);color:var(--text);cursor:pointer}.exception-node:hover{background:var(--panel3);border-color:color-mix(in srgb,var(--accent) 55%,var(--border))}.exception-node.selected{border-color:var(--accent);box-shadow:inset 3px 0 0 var(--accent)}.exception-role{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.exception-type{margin-top:5px;font:700 12px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--danger)}.exception-message{margin-top:4px;font:11px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--text);overflow-wrap:anywhere}.exception-location{margin-top:6px;font:10px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.exception-notes{margin-top:7px;padding:7px 8px;border-radius:8px;background:rgba(251,191,36,.07);color:var(--warning);font-size:10px;line-height:1.45}.exception-relation{display:flex;align-items:center;gap:8px;padding:7px 10px;color:var(--muted);font-size:10px}.exception-relation::before{content:"";width:1px;height:16px;background:var(--border);margin-left:8px}.chain-warning{margin-top:9px;padding:9px;border:1px solid rgba(251,191,36,.25);border-radius:9px;background:rgba(251,191,36,.07);color:var(--warning);font-size:10px}.transport{position:fixed;z-index:20;inset:auto 0 0;height:var(--transport);border-top:1px solid var(--border);background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(18px);padding:10px 18px}.transport-top{display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:14px}.controls{display:flex;gap:6px}.icon-btn{width:36px;height:36px;border:1px solid var(--border);border-radius:10px;background:var(--panel2);color:var(--text);cursor:pointer}.icon-btn:hover{background:var(--panel3)}.timeline-wrap{min-width:0}.timeline-meta{display:flex;justify-content:space-between;color:var(--muted);font:10px ui-monospace,SFMono-Regular,Consolas,monospace;margin-bottom:4px}input[type=range]{width:100%;accent-color:var(--accent);cursor:pointer}.speed{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:11px}.speed select{height:32px;border:1px solid var(--border);border-radius:8px;background:var(--panel2);color:var(--text)}.stats{margin-top:9px;display:flex;gap:14px;align-items:center;color:var(--muted);font:10px ui-monospace,SFMono-Regular,Consolas,monospace;white-space:nowrap;overflow:hidden}.stats span{overflow:hidden;text-overflow:ellipsis}.toast{position:fixed;z-index:40;right:18px;bottom:132px;padding:10px 13px;border:1px solid var(--border);border-radius:10px;background:var(--panel3);box-shadow:var(--shadow);font-size:12px;opacity:0;transform:translateY(6px);pointer-events:none;transition:.18s}.toast.show{opacity:1;transform:none}
@media(max-width:900px){:root{--header:112px;--transport:126px}.app-header{height:var(--header);align-items:flex-start;padding-top:12px;flex-wrap:wrap}.brand{width:calc(100% - 56px)}.header-actions{width:100%;overflow-x:auto;padding-bottom:8px}.workspace{grid-template-columns:1fr;grid-template-rows:minmax(280px,1.1fr) minmax(300px,1fr)}.right{grid-template-columns:1fr 1fr;grid-template-rows:1fr}.shortcut-only{display:none}}
</style>
</head>
<body>
<header class="app-header">
  <div class="logo">R</div>
  <div class="brand"><h1 id="reportTitle">RewindPy</h1><div class="crash" id="crashText"></div></div>
  <div class="header-actions">
    <div class="seg"><button id="sliceView"></button><button id="allView"></button></div>
    <button class="btn" id="openSource"></button>
    <button class="btn" id="copyDiagnostic"></button>
    <button class="btn" id="copyLocation"></button>
    <button class="btn" id="themeToggle">☀</button>
    <button class="btn" id="languageToggle">中文</button>
  </div>
</header>
<main class="workspace">
  <section class="panel">
    <div class="panel-head"><div class="panel-title" id="sourceTitle"></div><div class="file-name" id="fileName"></div></div>
    <div class="code-scroll" id="codeScroll"><div id="code"></div></div>
  </section>
  <section class="right">
    <section class="panel">
      <div class="panel-head"><div class="panel-title" id="currentEventTitle"></div><div class="file-name" id="eventBadge"></div></div>
      <div class="event-card">
        <div class="event-grid">
          <div class="metric"><label id="functionLabel"></label><b id="functionValue"></b></div>
          <div class="metric"><label id="locationLabel"></label><b id="locationValue"></b></div>
          <div class="metric"><label id="eventLabel"></label><b id="eventValue"></b></div>
          <div class="metric"><label id="depthLabel"></label><b id="depthValue"></b></div>
        </div>
        <div class="origin" id="originCard"><h3 id="originTitle"></h3><p id="originText"></p><button class="btn" id="jumpOrigin"></button></div>
      </div>
    </section>
    <section class="panel">
      <div class="panel-head"><div class="tabs"><button class="tab active" data-tab="variables" id="variablesTab"></button><button class="tab" data-tab="changes" id="changesTab"></button><button class="tab" data-tab="stack" id="stackTab"></button><button class="tab" data-tab="exceptions" id="exceptionsTab"></button></div><div class="file-name shortcut-only" id="shortcuts"></div></div>
      <div class="tab-body" id="tabBody"></div>
    </section>
  </section>
</main>
<footer class="transport">
  <div class="transport-top">
    <div class="controls"><button class="icon-btn" id="prev" title="Previous">◀</button><button class="icon-btn" id="play" title="Play">▶</button><button class="icon-btn" id="next" title="Next">▶|</button></div>
    <div class="timeline-wrap"><div class="timeline-meta"><span id="timelineTitle"></span><span id="stepText"></span></div><input id="slider" type="range" min="0" max="0" value="0" /></div>
    <div class="speed"><span id="speedLabel"></span><select id="speed"><option value="900">0.5×</option><option value="450" selected>1×</option><option value="220">2×</option><option value="90">4×</option></select></div>
  </div>
  <div class="stats" id="stats"></div>
</footer>
<div class="toast" id="toast"></div>
<script id="rewind-data" type="application/json">__DATA__</script>
<script>
(()=>{
const CURRENT_REPORT_SCHEMA=2;
function showReportError(error,raw){const schema=raw&&raw.schema_version!=null?Number(raw.schema_version):1;const newer=Number.isInteger(schema)&&schema>CURRENT_REPORT_SCHEMA;const title=newer?'This report requires a newer RewindPy':'The report data is invalid';const titleZh=newer?'此报告需要更新版本的 RewindPy':'报告数据无效';const detail=String(error&&error.message?error.message:error||'Unknown error').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));document.body.innerHTML=`<main style="min-height:100vh;display:grid;place-items:center;padding:28px;background:#080a10;color:#eef2ff;font-family:Inter,system-ui,sans-serif"><section style="width:min(680px,100%);border:1px solid #263247;border-radius:18px;background:#0d111a;padding:28px;box-shadow:0 20px 60px rgba(0,0,0,.35)"><div style="color:#fb7185;font-weight:800;font-size:13px;letter-spacing:.08em;text-transform:uppercase">RewindPy report error</div><h1 style="margin:12px 0 6px;font-size:24px">${title}</h1><h2 style="margin:0 0 18px;color:#8e9bb0;font-size:16px">${titleZh}</h2><pre style="margin:0;padding:14px;border:1px solid #263247;border-radius:12px;background:#121824;color:#fbbf24;white-space:pre-wrap;word-break:break-word">${detail}</pre><p style="margin:18px 0 0;color:#8e9bb0;line-height:1.6">Schema ${Number.isFinite(schema)?schema:'?'} · Viewer ${CURRENT_REPORT_SCHEMA}<br>请使用生成该报告的 RewindPy 版本，或升级 RewindPy 后重新生成报告。</p></section></main>`}
function normalizePayload(raw){if(!raw||typeof raw!=='object'||Array.isArray(raw))throw new Error('report payload must be an object');const schema=raw.schema_version==null?1:Number(raw.schema_version);if(!Number.isInteger(schema)||schema<1)throw new Error('schema_version must be a positive integer');if(schema>CURRENT_REPORT_SCHEMA)throw new Error(`unsupported report schema ${schema}; this viewer supports up to ${CURRENT_REPORT_SCHEMA}`);const object=value=>value&&typeof value==='object'&&!Array.isArray(value);if(schema===CURRENT_REPORT_SCHEMA){if(typeof raw.rewindpy_version!=='string'||!raw.rewindpy_version)throw new Error('rewindpy_version must be a non-empty string');if(!Array.isArray(raw.events))throw new Error('events must be an array');if(!object(raw.sources))throw new Error('sources must be an object');if(!object(raw.crash))throw new Error('crash must be an object');if(!object(raw.trace_stats))throw new Error('trace_stats must be an object');if(!object(raw.exception_chain)||!Array.isArray(raw.exception_chain.items))throw new Error('exception_chain.items must be an array')}const crash=object(raw.crash)?raw.crash:{};const fallback={index:0,exception_type:crash.exception_type||'Exception',exception_module:'builtins',message:crash.message||'',relation_to_next:null,suppress_context:false,file:crash.file??null,line:crash.line??null,function:crash.function??null,traceback:Array.isArray(crash.traceback)?crash.traceback:[],notes:[],event_step:null};const chain=object(raw.exception_chain)?raw.exception_chain:{items:[fallback],truncated:false,cycle_detected:false,max_depth:16};if(!Array.isArray(chain.items)||!chain.items.length)chain.items=[fallback];return{...raw,schema_version:CURRENT_REPORT_SCHEMA,events:Array.isArray(raw.events)?raw.events:[],sources:object(raw.sources)?raw.sources:{},crash,exception_chain:chain,trace_stats:object(raw.trace_stats)?raw.trace_stats:{},crash_slice:object(raw.crash_slice)?raw.crash_slice:{steps:[]}}}
let rawPayload=null;let payload=null;try{rawPayload=JSON.parse(document.getElementById('rewind-data').textContent);payload=normalizePayload(rawPayload)}catch(error){showReportError(error,rawPayload);return}
const translations=payload.translations||{};
let language=payload.language==='zh'?'zh':'en';let mode='slice';let events=[];let index=0;let playing=false;let timer=null;let activeTab='variables';let selectedException=0;
const $=id=>document.getElementById(id);const tr=k=>((translations[language]||translations.en||{})[k]||k);
const allEvents=payload.events||[];const sliceSteps=new Set((payload.crash_slice&&payload.crash_slice.steps)||[]);
function eventStepEnd(event){return event.step_end??event.step} // report guard compatibility
function selectEvents(){if(mode==='all'||!sliceSteps.size)return allEvents;return allEvents.filter(e=>sliceSteps.has(e.step)||sliceSteps.has(eventStepEnd(e)))}
function escapeHtml(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function highlight(line){let s=escapeHtml(line);s=s.replace(/(#.*)$/g,'<span class="com">$1</span>');s=s.replace(/(&quot;.*?&quot;|&#39;.*?&#39;)/g,'<span class="str">$1</span>');s=s.replace(/\b(def|return|for|in|if|else|elif|class|import|from|as|try|except|raise|with|None|True|False|and|or|not)\b/g,'<span class="kw">$1</span>');s=s.replace(/\b(\d+(?:\.\d+)?)\b/g,'<span class="num">$1</span>');s=s.replace(/\b([A-Za-z_]\w*)(?=\()/g,'<span class="fn">$1</span>');return s}
function current(){return events[index]||null}
function sourceFor(file){const sources=payload.sources||{};const normalized=String(file??'').replaceAll('\\','/');return sources[file]??sources[normalized]??Object.entries(sources).find(([key])=>String(key).replaceAll('\\','/')===normalized)?.[1]??''}
function sourceLines(source){if(Array.isArray(source))return source.map(line=>String(line??''));if(typeof source==='string')return source.split(/\r?\n/);if(source&&typeof source==='object'){if(Array.isArray(source.lines))return source.lines.map(line=>String(line??''));if(Array.isArray(source.source))return source.source.map(line=>String(line??''));if(typeof source.source==='string')return source.source.split(/\r?\n/);if(Array.isArray(source.content))return source.content.map(line=>String(line??''));if(typeof source.content==='string')return source.content.split(/\r?\n/);}return[]}
function renderCode(event){const root=$('code');const source=sourceFor(event?.file);$('fileName').textContent=event?.file||'';const lines=sourceLines(source);if(!lines.length){root.innerHTML=`<div style="padding:18px;color:var(--muted)">${tr('no_source')}</div>`;return}const crashLine=payload.crash?.line;const originLine=payload.analysis?.origin_line;root.innerHTML=lines.map((line,i)=>{const n=i+1;const cls=['code-line'];if(n===event.line)cls.push('active');if(n===crashLine&&event.file===payload.crash?.file)cls.push('crash-line');if(n===originLine&&event.file===payload.analysis?.origin_file)cls.push('origin-line');return `<div class="${cls.join(' ')}" data-line="${n}"><span class="arrow">▶</span><span class="line-no">${n}</span><span class="code">${highlight(line)}</span></div>`}).join('');requestAnimationFrame(()=>{const active=root.querySelector('.active');if(active){const scroller=$('codeScroll');const top=active.offsetTop-scroller.clientHeight/2;scroller.scrollTo({top:Math.max(0,top),behavior:'smooth'})}})}
function valueType(v){if(v===null)return'NoneType';if(Array.isArray(v))return'list';return typeof v==='object'?(v.type||'object'):typeof v}
function valueText(v){if(v&&typeof v==='object'&&'repr'in v)return v.repr;try{return typeof v==='string'?v:JSON.stringify(v,null,2)}catch{return String(v)}}
function renderVariables(event){const locals=event?.locals||{};const changed=new Set(Object.keys(event?.changes||{}));const entries=Object.entries(locals);if(!entries.length)return `<div style="color:var(--muted);padding:8px">${tr('no_variables')}</div>`;return entries.map(([name,v])=>`<div class="variable ${changed.has(name)?'changed':''}"><div class="var-top"><span class="var-name">${escapeHtml(name)}</span><span class="var-type">${escapeHtml(valueType(v))}</span></div><div class="var-value">${escapeHtml(valueText(v))}</div></div>`).join('')}
function renderChanges(event){const entries=Object.entries(event?.changes||{});if(!entries.length)return `<div style="color:var(--muted);padding:8px">${tr('no_changes')}</div>`;return entries.map(([name,d])=>`<div class="change"><b>${escapeHtml(name)}</b><div class="before">− ${escapeHtml(valueText(d.before))}</div><div class="after">+ ${escapeHtml(valueText(d.after))}</div></div>`).join('')}
function stackAt(idx){const frames=[];for(let i=0;i<=idx;i++){const e=events[i];if(e.event==='call')frames.push(e);if(e.event==='return'&&frames.length)frames.pop()}const now=events[idx];if(now&&!frames.some(f=>f.function===now.function&&f.depth===now.depth))frames.push(now);return frames}
function renderStack(){const frames=stackAt(index);return frames.slice().reverse().map(frame=>`<div class="frame" data-step="${frame.step}"><span class="frame-depth">${frame.depth}</span><div class="frame-main"><div class="frame-fn">${escapeHtml(frame.function)}()</div><div class="frame-loc">${escapeHtml(frame.file)}:${frame.line}</div></div></div>`).join('')}
function exceptionItems(){return Array.isArray(payload.exception_chain?.items)?payload.exception_chain.items:[]}
function exceptionLocation(item){return item?.file?`${item.file}:${item.line??'—'}`:''}
function renderExceptions(){const items=exceptionItems();if(!items.length)return `<div style="color:var(--muted);padding:8px">${tr('no_exception_chain')}</div>`;const nodes=items.map((item,i)=>{const role=items.length===1?tr('root_exception'):i===0?tr('outer_exception'):i===items.length-1?tr('root_exception'):`#${i+1}`;const notes=(item.notes||[]).length?`<div class="exception-notes"><b>${tr('exception_notes')}:</b> ${item.notes.map(escapeHtml).join('<br>')}</div>`:'';const relation=item.relation_to_next?`<div class="exception-relation">${item.relation_to_next==='cause'?tr('caused_by'):tr('during_handling')}</div>`:'';return `<button class="exception-node ${i===selectedException?'selected':''}" data-exception-index="${i}"><div class="exception-role">${escapeHtml(role)}</div><div class="exception-type">${escapeHtml(item.exception_type||'Exception')}</div><div class="exception-message">${escapeHtml(item.message||'')}</div><div class="exception-location">${escapeHtml(exceptionLocation(item)||'—')}</div>${notes}</button>${relation}`}).join('');const warnings=[payload.exception_chain?.truncated?tr('chain_truncated'):'',payload.exception_chain?.cycle_detected?tr('chain_cycle'):''].filter(Boolean).map(value=>`<div class="chain-warning">${escapeHtml(value)}</div>`).join('');return `<div class="exception-chain">${nodes}${warnings}</div>`}
function jumpException(nextIndex){const items=exceptionItems();const item=items[nextIndex];if(!item)return;selectedException=nextIndex;if(Number.isInteger(item.event_step)){jumpStep(item.event_step);return}const locate=()=>events.findIndex(event=>event.file===item.file&&event.line===item.line);let found=locate();if(found<0&&mode==='slice'){setMode('all');found=locate()}if(found>=0){index=found;render()}else renderTab(current())}
function renderTab(event){$('tabBody').innerHTML=activeTab==='variables'?renderVariables(event):activeTab==='changes'?renderChanges(event):activeTab==='stack'?renderStack():renderExceptions();document.querySelectorAll('.frame').forEach(el=>el.onclick=()=>jumpStep(Number(el.dataset.step)));document.querySelectorAll('.exception-node').forEach(el=>el.onclick=()=>jumpException(Number(el.dataset.exceptionIndex)))}
function renderOrigin(){const a=payload.analysis;const card=$('originCard');if(!a){$('originText').textContent=tr('no_origin');$('jumpOrigin').style.display='none';return}card.style.display='block';$('originText').textContent=a.summary||a.reason||tr('no_origin');$('jumpOrigin').style.display=a.origin_step==null?'none':'inline-flex'}
function render(){const event=current();if(!event)return;renderCode(event);renderTab(event);$('functionValue').textContent=event.function||'—';$('locationValue').textContent=`${event.file||'—'}:${event.line||'—'}`;$('eventValue').textContent=event.repeat_count?`${event.event} · ${tr('repeat')} ${event.repeat_count} ${tr('times')}`:event.event;$('depthValue').textContent=String(event.depth??0);$('eventBadge').textContent=`#${event.step}`;$('slider').value=String(index);$('stepText').textContent=`${tr('step')} ${index+1} ${tr('of')} ${events.length}`}
function setMode(next,keepStep){const step=keepStep??current()?.step;mode=next;events=selectEvents();index=Math.max(0,events.findIndex(e=>e.step===step));if(index<0)index=events.length-1;$('slider').max=String(Math.max(0,events.length-1));$('sliceView').classList.toggle('active',mode==='slice');$('allView').classList.toggle('active',mode==='all');render()}
function jumpStep(step){let found=events.findIndex(e=>e.step===step||eventStepEnd(e)===step);if(found<0&&mode==='slice'){setMode('all',step);found=events.findIndex(e=>e.step===step||eventStepEnd(e)===step)}if(found>=0){index=found;render()}}
function move(delta){index=Math.min(events.length-1,Math.max(0,index+delta));render();if(index===events.length-1&&playing)togglePlay(false)}
function togglePlay(force){playing=force??!playing;$('play').textContent=playing?'❚❚':'▶';clearInterval(timer);if(playing)timer=setInterval(()=>move(1),Number($('speed').value))}
function sourceUri(){const e=current();if(!e)return'';let path=e.file||'';if(payload.project_root&&!/^(?:[A-Za-z]:[\\/]|\/)/.test(path))path=payload.project_root.replace(/[\\/]$/,'')+'/'+path;return `vscode://file/${encodeURI(path.replaceAll('\\','/'))}:${e.line||1}`}
function openCurrentSource(){const uri=sourceUri();if(uri)window.location.href=uri}
function locationText(){const e=current();return e?`${e.file}:${e.line}`:''}
function diagnosticText(){const e=current();const chain=exceptionItems().map((item,i)=>`${i?'  '.repeat(i)+'↳ ':''}${item.exception_type||'Exception'}: ${item.message||''}`).join('\n');return [chain||`${payload.crash?.exception_type||'Error'}: ${payload.crash?.message||''}`,locationText(),payload.analysis?.summary||'',`step=${e?.step??''}`].filter(Boolean).join('\n')}
async function copy(text){try{await navigator.clipboard.writeText(text);toast(tr('copied'))}catch{toast(tr('copy_failed'))}}
function toast(message){const el=$('toast');el.textContent=message;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),1200)}
function statsText(){const s=payload.trace_stats||{};const parts=[`${s.retained_events??allEvents.length} ${tr('retained')}`,`${s.discarded_events??0} ${tr('discarded')}`,`${s.compressed_events??0} ${tr('compressed')}`,`${s.report_trimmed_events??0} ${tr('trimmed')}`,`${s.traced_files??0} ${tr('files')}`,`${Number(s.duration_seconds??0).toFixed(3)}s ${tr('trace_time')}`,`${((s.report_size_bytes??0)/1024).toFixed(1)}KB ${tr('report_size')}`];$('stats').innerHTML=parts.map(x=>`<span>${x}</span>`).join('')}
function applyLanguage(){document.documentElement.lang=language;$('reportTitle').textContent=tr('report_title');$('sourceTitle').textContent=tr('source');$('currentEventTitle').textContent=tr('current_event');$('functionLabel').textContent=tr('function');$('locationLabel').textContent=tr('location');$('eventLabel').textContent=tr('event');$('depthLabel').textContent=tr('depth');$('variablesTab').textContent=tr('variables');$('changesTab').textContent=tr('changes');$('stackTab').textContent=tr('call_stack');$('exceptionsTab').textContent=`${tr('exception_chain')} · ${exceptionItems().length}`;$('originTitle').textContent=tr('origin');$('jumpOrigin').textContent=tr('jump_origin');$('sliceView').textContent=tr('crash_slice');$('allView').textContent=tr('all_events');$('openSource').textContent=tr('open_source');$('copyDiagnostic').textContent=tr('copy_diagnostic');$('copyLocation').textContent=tr('copy_location');$('timelineTitle').textContent=tr('timeline');$('speedLabel').textContent=tr('speed');$('shortcuts').textContent=tr('shortcuts');$('languageToggle').textContent=language==='en'?'中文':'EN';renderOrigin();statsText();render()}
$('slider').oninput=e=>{index=Number(e.target.value);render()};$('prev').onclick=()=>move(-1);$('next').onclick=()=>move(1);$('play').onclick=()=>togglePlay();$('speed').onchange=()=>{if(playing)togglePlay(true)};$('sliceView').onclick=()=>setMode('slice');$('allView').onclick=()=>setMode('all');$('languageToggle').onclick=()=>{language=language==='en'?'zh':'en';applyLanguage()};$('themeToggle').onclick=()=>{const root=document.documentElement;root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';$('themeToggle').textContent=root.dataset.theme==='dark'?'☀':'☾'};$('openSource').onclick=openCurrentSource;$('copyDiagnostic').onclick=()=>copy(diagnosticText());$('copyLocation').onclick=()=>copy(locationText());$('jumpOrigin').onclick=()=>jumpStep(Number(payload.analysis?.origin_step));document.querySelectorAll('.tab').forEach(tab=>tab.onclick=()=>{activeTab=tab.dataset.tab;document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t===tab));renderTab(current())});document.addEventListener('keydown',event=>{if(['INPUT','SELECT','TEXTAREA'].includes(event.target.tagName))return;const key=event.key.toLowerCase();if(event.key==='ArrowLeft'||key==='j'){event.preventDefault();move(-1)}if(event.key==='ArrowRight'||key==='k'){event.preventDefault();move(1)}if(event.code==='Space'){event.preventDefault();togglePlay()}if (key === 'o') openCurrentSource();if (key === 'c') copy(diagnosticText());if (key === 'l') copy(locationText())});
$('crashText').textContent=`${payload.crash?.exception_type||'Error'}: ${payload.crash?.message||''}`;renderOrigin();setMode('slice');applyLanguage();
})();
</script>
</body>
</html>'''


def write_report(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = prepare_report_payload(payload)
    verify_report_integrity(document)
    document["translations"] = _REPORT_MESSAGES
    encoded = json.dumps(document, ensure_ascii=False).replace("</", "<\\/")
    output_path.write_text(HTML_TEMPLATE.replace("__DATA__", encoded), encoding="utf-8")
