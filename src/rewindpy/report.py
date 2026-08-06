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
.header-tools { display:flex; align-items:center; justify-content:flex-end; flex-wrap:wrap; gap:8px; }
.view-switch { display:flex; gap:4px; padding:3px; border:1px solid #334262; border-radius:10px; background:#11182b; }
.view-button { border:0; background:transparent; color:#9fb0d6; }
.view-button.active { background:#2c4170; color:#fff; }
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
.origin { margin:14px 16px; padding:14px; border:1px solid #5b6f9f; border-radius:12px; background:#182440; }
.origin-title { font-weight:800; margin-bottom:8px; color:#dce7ff; }
.origin-summary { color:#bed0f7; line-height:1.55; margin-bottom:10px; }
.origin-location { font:12px ui-monospace, SFMono-Regular, Consolas, monospace; color:#8fa2cf; margin-bottom:10px; }
.origin-hint { color:#ffd99b; margin-top:8px; }
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
button:disabled { cursor:not-allowed; opacity:.45; }
#stepLabel { min-width:240px; text-align:center; font:12px ui-monospace, SFMono-Regular, Consolas, monospace; color:#b8c7ea; }
#location { margin-top:8px; font:12px ui-monospace, SFMono-Regular, Consolas, monospace; color:#8fa2cf; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
@media (max-width: 850px) {
  header { align-items:flex-start; flex-direction:column; }
  main { grid-template-columns:1fr; height:auto; }
  .panel { min-height:45vh; border-right:0; border-bottom:1px solid #26304c; }
  #stepLabel { min-width:150px; }
}
</style>
</head>
<body>
<header>
  <div><h1>⏪ RewindPy</h1><div class="crash" id="crashTitle"></div></div>
  <div class="header-tools">
    <div class="view-switch" aria-label="Timeline view">
      <button class="view-button" id="sliceView">Crash Slice</button>
      <button class="view-button" id="allView">All Events</button>
    </div>
    <span class="badge">local report</span>
    <span class="badge" id="eventCount"></span>
  </div>
</header>
<main>
  <section class="panel">
    <div class="panel-title" id="fileTitle">Source</div>
    <pre id="code"></pre>
  </section>
  <section class="panel">
    <div class="panel-title">Execution state</div>
    <div class="meta" id="eventMeta"></div>
    <div class="panel-title">Likely origin</div>
    <div id="origin"></div>
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
const allEvents = data.events || [];
const sources = data.sources || {};
const crash = data.crash || {};
const analysis = data.analysis || null;
const crashSlice = data.crash_slice || {};
const sliceSteps = new Set(crashSlice.steps || []);
const slider = document.getElementById('slider');
const sliceButton = document.getElementById('sliceView');
const allButton = document.getElementById('allView');
let mode = sliceSteps.size ? 'slice' : 'all';
let events = eventsForMode(mode);

document.getElementById('crashTitle').textContent = `${crash.exception_type || 'Exception'}: ${crash.message || ''}`;

function eventsForMode(nextMode) {
  if (nextMode === 'slice' && sliceSteps.size) {
    return allEvents.filter(event => sliceSteps.has(event.step));
  }
  return allEvents;
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
}
function pretty(value) { return JSON.stringify(value, null, 2); }
function nearestIndex(step) {
  if (!events.length) return 0;
  let bestIndex = 0;
  let bestDistance = Number.POSITIVE_INFINITY;
  events.forEach((event, index) => {
    const distance = Math.abs(Number(event.step) - Number(step));
    if (distance < bestDistance) {
      bestDistance = distance;
      bestIndex = index;
    }
  });
  return bestIndex;
}
function updateViewControls() {
  sliceButton.classList.toggle('active', mode === 'slice');
  allButton.classList.toggle('active', mode === 'all');
  sliceButton.disabled = !sliceSteps.size;
  const label = mode === 'slice' ? 'Crash Slice' : 'All Events';
  document.getElementById('eventCount').textContent = `${label} · ${events.length} of ${allEvents.length} events`;
}
function setView(nextMode, preferredStep = null) {
  const currentEvent = events[Number(slider.value)] || events[events.length - 1];
  const step = preferredStep ?? currentEvent?.step ?? allEvents[allEvents.length - 1]?.step ?? 0;
  mode = nextMode === 'slice' && sliceSteps.size ? 'slice' : 'all';
  events = eventsForMode(mode);
  slider.max = Math.max(0, events.length - 1);
  slider.value = nearestIndex(step);
  updateViewControls();
  render(Number(slider.value));
}
function renderCode(event) {
  const lines = sources[event.file] || [];
  const html = lines.map((line, i) => `<span class="code-line ${i + 1 === event.line ? 'active' : ''}" data-line="${i + 1}">${escapeHtml(line)}</span>`).join('\n');
  document.getElementById('code').innerHTML = html || '<span class="empty">Source unavailable.</span>';
  document.getElementById('fileTitle').textContent = event.file;
  const active = document.querySelector('.code-line.active');
  if (active) active.scrollIntoView({block:'center'});
}
function renderOrigin() {
  const container = document.getElementById('origin');
  if (!analysis) {
    container.innerHTML = '<div class="empty">No earlier value origin was identified for this crash.</div>';
    return;
  }
  const replacement = analysis.likely_replacement
    ? `<div class="origin-hint">Possible rename: <code>${escapeHtml(analysis.missing_key)}</code> → <code>${escapeHtml(analysis.likely_replacement)}</code></div>`
    : '';
  const noneHint = analysis.kind === 'none-value-origin'
    ? `<div class="origin-hint">${analysis.producer_function
        ? `Produced by <code>${escapeHtml(analysis.producer_function)}()</code> returning <code>None</code>.`
        : `<code>${escapeHtml(analysis.variable)}</code> was assigned <code>None</code>.`}</div>`
    : '';
  container.innerHTML = `
    <div class="origin">
      <div class="origin-title">${escapeHtml(analysis.title || 'Probable cause found')}</div>
      <div class="origin-summary">${escapeHtml(analysis.summary)}</div>
      <div class="origin-location">${escapeHtml(analysis.file)}:${escapeHtml(analysis.line)} in ${escapeHtml(analysis.function)}()</div>
      <button id="jumpOrigin">Jump to step ${escapeHtml(analysis.origin_step)}</button>
      ${replacement}
      ${noneHint}
    </div>`;
  document.getElementById('jumpOrigin').onclick = () => {
    const targetMode = sliceSteps.has(analysis.origin_step) ? 'slice' : 'all';
    setView(targetMode, analysis.origin_step);
  };
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
  if (!events.length) {
    document.getElementById('code').innerHTML = '<span class="empty">No execution events were captured.</span>';
    return;
  }
  const safeIndex = Math.max(0, Math.min(index, events.length - 1));
  slider.value = safeIndex;
  const event = events[safeIndex];
  renderCode(event);
  renderChanges(event);
  document.getElementById('locals').textContent = pretty(event.locals || {});
  document.getElementById('eventMeta').innerHTML = [
    `<span class="badge">${escapeHtml(event.event)}</span>`,
    `<span class="badge">${escapeHtml(event.function)}</span>`,
    event.exception_type ? `<div class="crash">${escapeHtml(event.exception_type)}: ${escapeHtml(event.exception_message || '')}</div>` : ''
  ].join('');
  const viewLabel = mode === 'slice' ? 'Crash Slice' : 'All Events';
  document.getElementById('stepLabel').textContent = `Step ${event.step} · ${safeIndex + 1}/${events.length} · ${viewLabel}`;
  const changeLocation = event.change_line && Object.keys(event.changes || {}).length
    ? ` · changes caused by line ${event.change_line}`
    : '';
  document.getElementById('location').textContent = `${event.file}:${event.line} in ${event.function}()${changeLocation}`;
  document.getElementById('prev').disabled = safeIndex === 0;
  document.getElementById('next').disabled = safeIndex === events.length - 1;
}
slider.addEventListener('input', () => render(Number(slider.value)));
document.getElementById('prev').onclick = () => render(Number(slider.value) - 1);
document.getElementById('next').onclick = () => render(Number(slider.value) + 1);
sliceButton.onclick = () => setView('slice');
allButton.onclick = () => setView('all');
document.addEventListener('keydown', event => {
  if (event.key === 'ArrowLeft') document.getElementById('prev').click();
  if (event.key === 'ArrowRight') document.getElementById('next').click();
});
renderOrigin();
setView(mode, allEvents[allEvents.length - 1]?.step);
</script>
</body>
</html>
'''


def write_report(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    output_path.write_text(HTML_TEMPLATE.replace("__DATA__", encoded), encoding="utf-8")
