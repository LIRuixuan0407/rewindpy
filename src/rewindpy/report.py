from __future__ import annotations

import json
from pathlib import Path
from typing import Any


HTML_TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>RewindPy crash report</title>
<style>
:root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
* { box-sizing: border-box; }
body { margin: 0; background: #0b1020; color: #edf2ff; }
header { padding: 18px 24px; border-bottom: 1px solid #26304c; display:flex; align-items:center; justify-content:space-between; gap:18px; }
h1 { margin:0; font-size:20px; }
.crash { color:#ff9b9b; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
main { display:grid; grid-template-columns: minmax(420px, 1.5fr) minmax(300px, 1fr); height: calc(100vh - 150px); }
.panel { min-width:0; border-right:1px solid #26304c; overflow:auto; }
.panel:last-child { border-right:0; }
.panel-title { position:sticky; top:0; z-index:2; background:#11182b; padding:10px 16px; border-bottom:1px solid #26304c; font-size:13px; color:#aebce0; }
#code { margin:0; padding:14px 0 40px; font:13px/1.7 ui-monospace, SFMono-Regular, Consolas, monospace; white-space:pre; }
.code-line { display:block; padding:0 16px; min-height:22px; }
.code-line::before { display:inline-block; width:48px; margin-right:14px; text-align:right; color:#607099; content:attr(data-line); }
.code-line.active { background:#263a68; box-shadow: inset 3px 0 #75a7ff; }
.meta { padding:14px 16px; border-bottom:1px solid #26304c; font:13px/1.6 ui-monospace, SFMono-Regular, Consolas, monospace; }
.badge { display:inline-block; border:1px solid #3d4b70; border-radius:999px; padding:2px 8px; margin-right:6px; color:#bfd0ff; }
pre { white-space:pre-wrap; word-break:break-word; }
.change { border-bottom:1px solid #26304c; padding:10px 16px; }
.change-name { font-weight:700; margin-bottom:6px; }
.before { color:#ffabab; }
.after { color:#a8efb7; }
.empty { color:#7381a5; padding:16px; }
footer { height:84px; border-top:1px solid #26304c; padding:12px 24px; background:#0e1528; }
.timeline { display:flex; align-items:center; gap:14px; }
input[type=range] { width:100%; }
button { background:#1d2b4b; color:#edf2ff; border:1px solid #39496f; border-radius:8px; padding:6px 10px; cursor:pointer; }
button:hover { background:#26385f; }
#stepLabel { min-width:170px; text-align:center; font:12px ui-monospace, SFMono-Regular, Consolas, monospace; color:#b8c7ea; }
#location { margin-top:8px; font:12px ui-monospace, SFMono-Regular, Consolas, monospace; color:#8fa2cf; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
</style>
</head>
<body>
<header>
  <div><h1>⏪ RewindPy</h1><div class="crash" id="crashTitle"></div></div>
  <div><span class="badge">local report</span><span class="badge" id="eventCount"></span></div>
</header>
<main>
  <section class="panel">
    <div class="panel-title" id="fileTitle">Source</div>
    <pre id="code"></pre>
  </section>
  <section class="panel">
    <div class="panel-title">Execution state</div>
    <div class="meta" id="eventMeta"></div>
    <div class="panel-title">Variable changes</div>
    <div id="changes"></div>
    <div class="panel-title">Locals snapshot</div>
    <pre class="meta" id="locals"></pre>
  </section>
</main>
<footer>
  <div class="timeline">
    <button id="prev">◀</button>
    <input id="slider" type="range" min="0" value="0" />
    <button id="next">▶</button>
    <div id="stepLabel"></div>
  </div>
  <div id="location"></div>
</footer>
<script id="rewind-data" type="application/json">__DATA__</script>
<script>
const data = JSON.parse(document.getElementById('rewind-data').textContent);
const events = data.events || [];
const sources = data.sources || {};
const crash = data.crash || {};
const slider = document.getElementById('slider');
slider.max = Math.max(0, events.length - 1);
slider.value = Math.max(0, events.length - 1);
document.getElementById('eventCount').textContent = `${events.length} events`;
document.getElementById('crashTitle').textContent = `${crash.exception_type || 'Exception'}: ${crash.message || ''}`;

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
}
function pretty(value) { return JSON.stringify(value, null, 2); }
function renderCode(event) {
  const lines = sources[event.file] || [];
  const html = lines.map((line, i) => `<span class="code-line ${i + 1 === event.line ? 'active' : ''}" data-line="${i + 1}">${escapeHtml(line)}</span>`).join('\n');
  document.getElementById('code').innerHTML = html || '<span class="empty">Source unavailable.</span>';
  document.getElementById('fileTitle').textContent = event.file;
  const active = document.querySelector('.code-line.active');
  if (active) active.scrollIntoView({block:'center'});
}
function renderChanges(event) {
  const changes = event.changes || {};
  const container = document.getElementById('changes');
  const names = Object.keys(changes);
  if (!names.length) {
    container.innerHTML = '<div class="empty">No local variable changes on this step.</div>';
    return;
  }
  container.innerHTML = names.map(name => {
    const change = changes[name];
    return `<div class="change"><div class="change-name">${escapeHtml(name)}</div><pre class="before">- ${escapeHtml(pretty(change.before))}</pre><pre class="after">+ ${escapeHtml(pretty(change.after))}</pre></div>`;
  }).join('');
}
function render(index) {
  if (!events.length) return;
  const event = events[index];
  renderCode(event);
  renderChanges(event);
  document.getElementById('locals').textContent = pretty(event.locals || {});
  document.getElementById('eventMeta').innerHTML = [
    `<span class="badge">${escapeHtml(event.event)}</span>`,
    `<span class="badge">${escapeHtml(event.function)}</span>`,
    event.exception_type ? `<div class="crash">${escapeHtml(event.exception_type)}: ${escapeHtml(event.exception_message || '')}</div>` : ''
  ].join('');
  document.getElementById('stepLabel').textContent = `Step ${event.step} · ${index + 1}/${events.length}`;
  document.getElementById('location').textContent = `${event.file}:${event.line} in ${event.function}()`;
}
slider.addEventListener('input', () => render(Number(slider.value)));
document.getElementById('prev').onclick = () => { slider.value = Math.max(0, Number(slider.value) - 1); render(Number(slider.value)); };
document.getElementById('next').onclick = () => { slider.value = Math.min(events.length - 1, Number(slider.value) + 1); render(Number(slider.value)); };
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowLeft') document.getElementById('prev').click();
  if (e.key === 'ArrowRight') document.getElementById('next').click();
});
render(Number(slider.value));
</script>
</body>
</html>
'''


def write_report(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    output_path.write_text(HTML_TEMPLATE.replace("__DATA__", encoded), encoding="utf-8")
