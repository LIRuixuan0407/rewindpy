from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_REPORT_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "report_title": "RewindPy crash report",
        "timeline_view": "Timeline view",
        "crash_slice": "Crash Slice",
        "all_events": "All Events",
        "local_report": "local report",
        "source": "Source",
        "execution_state": "Execution state",
        "likely_origin": "Likely origin",
        "variable_changes": "Variable changes",
        "locals_snapshot": "Locals snapshot",
        "source_unavailable": "Source unavailable.",
        "no_origin": "No earlier value origin was identified for this crash.",
        "possible_rename": "Possible rename",
        "produced_by": "Produced by",
        "returning_none": "returning None",
        "assigned_none": "was assigned None",
        "jump_to_step": "Jump to step",
        "no_changes": "No local variable changes on this step.",
        "no_events": "No execution events were captured.",
        "step": "Step",
        "events": "events",
        "of": "of",
        "changes_caused": "changes caused by line",
        "probable_cause": "Probable cause found",
    },
    "zh": {
        "report_title": "RewindPy 崩溃报告",
        "timeline_view": "时间线视图",
        "crash_slice": "崩溃切片",
        "all_events": "全部事件",
        "local_report": "本地报告",
        "source": "源代码",
        "execution_state": "执行状态",
        "likely_origin": "可能来源",
        "variable_changes": "变量变化",
        "locals_snapshot": "局部变量快照",
        "source_unavailable": "无法获取源代码。",
        "no_origin": "没有为这次崩溃找到可信的更早数值来源。",
        "possible_rename": "可能的重命名",
        "produced_by": "来源函数",
        "returning_none": "返回了 None",
        "assigned_none": "被赋值为 None",
        "jump_to_step": "跳转到步骤",
        "no_changes": "这一步没有局部变量变化。",
        "no_events": "没有捕获到执行事件。",
        "step": "步骤",
        "events": "个事件",
        "of": "/",
        "changes_caused": "变量变化由代码行触发",
        "probable_cause": "已找到可能原因",
    },
}


HTML_TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>RewindPy crash report</title>
<style>
:root {
  color-scheme: dark;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --header-h: 76px;
  --footer-h: 104px;
  --bg: #080b12;
  --surface: #0f141f;
  --surface-2: #151b28;
  --surface-3: #1b2333;
  --border: rgba(148, 163, 184, .16);
  --border-strong: rgba(148, 163, 184, .28);
  --text: #f8fafc;
  --muted: #94a3b8;
  --soft: #cbd5e1;
  --accent: #7c8cff;
  --accent-2: #5eead4;
  --danger: #fb7185;
  --success: #86efac;
  --warning: #fbbf24;
  --shadow: 0 18px 50px rgba(0, 0, 0, .28);
}
* { box-sizing: border-box; }
html, body { width: 100%; height: 100%; overflow: hidden; }
body {
  margin: 0;
  background:
    radial-gradient(circle at 12% -10%, rgba(124, 140, 255, .14), transparent 34%),
    radial-gradient(circle at 88% 110%, rgba(94, 234, 212, .08), transparent 34%),
    var(--bg);
  color: var(--text);
}
button, input { font: inherit; }
header {
  position: fixed;
  inset: 0 0 auto 0;
  z-index: 30;
  height: var(--header-h);
  padding: 0 22px;
  border-bottom: 1px solid var(--border);
  background: rgba(8, 11, 18, .88);
  backdrop-filter: blur(18px);
  display: grid;
  grid-template-columns: minmax(260px, 1fr) auto;
  align-items: center;
  gap: 20px;
}
.brand { min-width: 0; display: flex; align-items: center; gap: 12px; }
.brand-mark {
  width: 38px; height: 38px; flex: 0 0 auto;
  display: grid; place-items: center;
  border: 1px solid rgba(124, 140, 255, .36);
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(124, 140, 255, .22), rgba(94, 234, 212, .08));
  box-shadow: inset 0 1px 0 rgba(255,255,255,.08);
  font-size: 18px;
}
.brand-copy { min-width: 0; }
h1 { margin: 0; font-size: 17px; line-height: 1.2; letter-spacing: -.02em; }
.crash {
  margin-top: 5px;
  color: var(--danger);
  font: 12px/1.3 ui-monospace, SFMono-Regular, Consolas, monospace;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.header-tools { display: flex; align-items: center; justify-content: flex-end; gap: 8px; }
.view-switch {
  display: grid; grid-template-columns: 1fr 1fr;
  width: 226px; height: 38px; padding: 3px;
  border: 1px solid var(--border);
  border-radius: 11px;
  background: rgba(15, 20, 31, .86);
}
.view-button, .language-toggle, .nav-button, .origin button {
  border: 0;
  color: var(--muted);
  cursor: pointer;
  transition: background .16s ease, color .16s ease, border-color .16s ease, transform .16s ease;
}
.view-button { border-radius: 8px; background: transparent; font-size: 12px; font-weight: 650; }
.view-button.active {
  color: var(--text);
  background: var(--surface-3);
  box-shadow: 0 1px 0 rgba(255,255,255,.05), 0 5px 16px rgba(0,0,0,.2);
}
.language-toggle {
  width: 78px; height: 38px; flex: 0 0 78px;
  border: 1px solid var(--border);
  border-radius: 11px;
  background: rgba(15, 20, 31, .86);
  color: var(--soft);
  font-size: 12px; font-weight: 750; letter-spacing: .02em;
}
.language-toggle:hover, .nav-button:hover, .origin button:hover { color: var(--text); border-color: var(--border-strong); background: var(--surface-3); }
.badge {
  display: inline-flex; align-items: center; height: 28px;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0 9px;
  color: var(--muted);
  background: rgba(15, 20, 31, .72);
  font-size: 11px; white-space: nowrap;
}
main {
  position: fixed;
  inset: var(--header-h) 0 var(--footer-h) 0;
  display: grid;
  grid-template-columns: minmax(420px, 1.45fr) minmax(340px, .9fr);
  gap: 1px;
  background: var(--border);
  overflow: hidden;
}
.panel { min-width: 0; min-height: 0; overflow: auto; background: rgba(15, 20, 31, .9); overscroll-behavior: contain; scrollbar-gutter: stable; }
.panel-title {
  position: sticky; top: 0; z-index: 4;
  min-height: 41px;
  display: flex; align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid var(--border);
  background: rgba(15, 20, 31, .94);
  backdrop-filter: blur(12px);
  color: var(--muted);
  font-size: 11px; font-weight: 750; letter-spacing: .08em; text-transform: uppercase;
}
#code { margin: 0; padding: 12px 0 48px; font: 13px/1.72 ui-monospace, SFMono-Regular, Consolas, monospace; white-space: pre; tab-size: 4; }
.code-line { display: block; min-height: 23px; padding: 0 20px 0 8px; border-left: 3px solid transparent; }
.code-line::before { display: inline-block; width: 50px; margin-right: 16px; text-align: right; color: #526076; content: attr(data-line); user-select: none; }
.code-line.active {
  border-left-color: var(--accent);
  background: linear-gradient(90deg, rgba(124, 140, 255, .18), rgba(124, 140, 255, .035));
  color: #fff;
}
.meta { padding: 14px 16px; border-bottom: 1px solid var(--border); font: 12px/1.65 ui-monospace, SFMono-Regular, Consolas, monospace; }
pre { white-space: pre-wrap; word-break: break-word; margin: 0; }
.origin { margin: 14px 16px; padding: 15px; border: 1px solid rgba(124, 140, 255, .3); border-radius: 14px; background: linear-gradient(145deg, rgba(124,140,255,.12), rgba(21,27,40,.86)); box-shadow: var(--shadow); }
.origin-title { margin-bottom: 8px; color: #eef2ff; font-size: 14px; font-weight: 800; }
.origin-summary { margin-bottom: 11px; color: var(--soft); font-size: 13px; line-height: 1.58; }
.origin-location { margin-bottom: 11px; color: var(--muted); font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; }
.origin-hint { margin-top: 10px; color: #fde68a; font-size: 12px; }
.origin button { min-height: 34px; padding: 0 11px; border: 1px solid rgba(124,140,255,.35); border-radius: 9px; background: rgba(124,140,255,.12); color: #dfe4ff; font-size: 12px; font-weight: 700; }
.change { border-bottom: 1px solid var(--border); padding: 12px 16px; }
.change-name { margin-bottom: 7px; font-size: 12px; font-weight: 800; color: var(--soft); }
.before { color: #fda4af; }
.after { color: var(--success); margin-top: 5px; }
.empty { color: #64748b; padding: 16px; font-size: 12px; }
footer {
  position: fixed;
  inset: auto 0 0 0;
  z-index: 35;
  height: var(--footer-h);
  padding: 14px 22px 12px;
  border-top: 1px solid var(--border);
  background: rgba(8, 11, 18, .94);
  backdrop-filter: blur(18px);
  box-shadow: 0 -16px 38px rgba(0, 0, 0, .24);
}
.timeline { display: grid; grid-template-columns: 36px minmax(120px, 1fr) 36px 250px; align-items: center; gap: 11px; }
.nav-button {
  width: 36px; height: 34px; padding: 0;
  border: 1px solid var(--border);
  border-radius: 9px;
  background: var(--surface-2);
  color: var(--soft);
}
.nav-button:disabled { cursor: not-allowed; opacity: .35; }
input[type=range] { width: 100%; accent-color: var(--accent); cursor: ew-resize; }
#stepLabel { width: 250px; text-align: right; font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; color: var(--soft); white-space: nowrap; }
#location { margin-top: 10px; padding-left: 94px; color: var(--muted); font: 11px ui-monospace, SFMono-Regular, Consolas, monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 920px) {
  :root { --header-h: 118px; --footer-h: 112px; }
  header { grid-template-columns: 1fr; align-content: center; gap: 10px; }
  .header-tools { justify-content: flex-start; }
  main { grid-template-columns: 1fr; grid-template-rows: 1fr 1fr; }
  .view-switch { width: 210px; }
  .timeline { grid-template-columns: 34px minmax(90px,1fr) 34px; }
  #stepLabel { grid-column: 1 / -1; width: auto; text-align: center; }
  #location { padding-left: 0; text-align: center; }
  #eventCount { display: none; }
}
</style>
</head>
<body>
<header>
  <div class="brand">
    <div class="brand-mark" aria-hidden="true">↶</div>
    <div class="brand-copy"><h1>RewindPy</h1><div class="crash" id="crashTitle"></div></div>
  </div>
  <div class="header-tools">
    <div class="view-switch" id="viewSwitch" aria-label="Timeline view">
      <button class="view-button" id="sliceView">Crash Slice</button>
      <button class="view-button" id="allView">All Events</button>
    </div>
    <button class="language-toggle" id="languageToggle" aria-label="Switch language">中文</button>
    <span class="badge" id="localReport">local report</span>
    <span class="badge" id="eventCount"></span>
  </div>
</header>
<main>
  <section class="panel" id="codePanel">
    <div class="panel-title" id="fileTitle">Source</div>
    <pre id="code"></pre>
  </section>
  <section class="panel">
    <div class="panel-title" id="executionStateTitle">Execution state</div>
    <div class="meta" id="eventMeta"></div>
    <div class="panel-title" id="likelyOriginTitle">Likely origin</div>
    <div id="origin"></div>
    <div class="panel-title" id="variableChangesTitle">Variable changes</div>
    <div id="changes"></div>
    <div class="panel-title" id="localsSnapshotTitle">Locals snapshot</div>
    <pre class="meta" id="locals"></pre>
  </section>
</main>
<footer>
  <div class="timeline">
    <button class="nav-button" id="prev" aria-label="Previous step">◀</button>
    <input id="slider" type="range" min="0" value="0" />
    <button class="nav-button" id="next" aria-label="Next step">▶</button>
    <div id="stepLabel"></div>
  </div>
  <div id="location"></div>
</footer>
<script id="rewind-data" type="application/json">__DATA__</script>
<script>
const data = JSON.parse(document.getElementById('rewind-data').textContent);
const translations = data.translations || {};
let language = data.language === 'zh' ? 'zh' : 'en';
function tr(key) { return (translations[language] || translations.en || {})[key] || key; }
function localized(object, field) {
  const values = object?.[`${field}_i18n`] || {};
  return values[language] || object?.[field] || '';
}
const allEvents = data.events || [];
const sources = data.sources || {};
const crash = data.crash || {};
const analysis = data.analysis || null;
const crashSlice = data.crash_slice || {};
const sliceSteps = new Set(crashSlice.steps || []);
const slider = document.getElementById('slider');
const sliceButton = document.getElementById('sliceView');
const allButton = document.getElementById('allView');
const languageToggle = document.getElementById('languageToggle');
const codePanel = document.getElementById('codePanel');
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
  const label = mode === 'slice' ? tr('crash_slice') : tr('all_events');
  document.getElementById('eventCount').textContent = `${label} · ${events.length} ${tr('of')} ${allEvents.length} ${tr('events')}`;
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
  document.getElementById('code').innerHTML = html || `<span class="empty">${escapeHtml(tr('source_unavailable'))}</span>`;
  document.getElementById('fileTitle').textContent = event.file;
  const active = document.querySelector('.code-line.active');
  if (active && codePanel) {
    const targetTop = active.offsetTop - (codePanel.clientHeight / 2) + (active.clientHeight / 2);
    codePanel.scrollTo({top: Math.max(0, targetTop), behavior: 'auto'});
  }
}
function renderOrigin() {
  const container = document.getElementById('origin');
  if (!analysis) {
    container.innerHTML = `<div class="empty">${escapeHtml(tr('no_origin'))}</div>`;
    return;
  }
  const replacement = analysis.likely_replacement
    ? `<div class="origin-hint">${escapeHtml(tr('possible_rename'))}: <code>${escapeHtml(analysis.missing_key)}</code> → <code>${escapeHtml(analysis.likely_replacement)}</code></div>`
    : '';
  const noneHint = analysis.kind === 'none-value-origin'
    ? `<div class="origin-hint">${analysis.producer_function
        ? `${escapeHtml(tr('produced_by'))} <code>${escapeHtml(analysis.producer_function)}()</code>，${escapeHtml(tr('returning_none'))}.`
        : `<code>${escapeHtml(analysis.variable)}</code> ${escapeHtml(tr('assigned_none'))}.`}</div>`
    : '';
  container.innerHTML = `
    <div class="origin">
      <div class="origin-title">${escapeHtml(localized(analysis, 'title') || tr('probable_cause'))}</div>
      <div class="origin-summary">${escapeHtml(localized(analysis, 'summary'))}</div>
      <div class="origin-location">${escapeHtml(analysis.file)}:${escapeHtml(analysis.line)} in ${escapeHtml(analysis.function)}()</div>
      <button id="jumpOrigin">${escapeHtml(tr('jump_to_step'))} ${escapeHtml(analysis.origin_step)}</button>
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
    container.innerHTML = `<div class="empty">${escapeHtml(tr('no_changes'))}</div>`;
    return;
  }
  container.innerHTML = names.map(name => {
    const change = changes[name];
    return `<div class="change"><div class="change-name">${escapeHtml(name)}</div><pre class="before">- ${escapeHtml(pretty(change.before))}</pre><pre class="after">+ ${escapeHtml(pretty(change.after))}</pre></div>`;
  }).join('');
}
function render(index) {
  if (!events.length) {
    document.getElementById('code').innerHTML = `<span class="empty">${escapeHtml(tr('no_events'))}</span>`;
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
  const viewLabel = mode === 'slice' ? tr('crash_slice') : tr('all_events');
  document.getElementById('stepLabel').textContent = `${tr('step')} ${event.step} · ${safeIndex + 1}/${events.length} · ${viewLabel}`;
  const changeLocation = event.change_line && Object.keys(event.changes || {}).length
    ? ` · ${tr('changes_caused')} ${event.change_line}`
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
function applyLanguage(nextLanguage) {
  language = nextLanguage === 'zh' ? 'zh' : 'en';
  document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en';
  document.title = tr('report_title');
  document.getElementById('viewSwitch').setAttribute('aria-label', tr('timeline_view'));
  sliceButton.textContent = tr('crash_slice');
  allButton.textContent = tr('all_events');
  document.getElementById('localReport').textContent = tr('local_report');
  document.getElementById('executionStateTitle').textContent = tr('execution_state');
  document.getElementById('likelyOriginTitle').textContent = tr('likely_origin');
  document.getElementById('variableChangesTitle').textContent = tr('variable_changes');
  document.getElementById('localsSnapshotTitle').textContent = tr('locals_snapshot');
  languageToggle.textContent = language === 'en' ? '中文' : 'EN';
  languageToggle.setAttribute('aria-label', language === 'en' ? '切换到中文' : 'Switch to English');
  renderOrigin();
  updateViewControls();
  render(Number(slider.value));
}
languageToggle.onclick = () => applyLanguage(language === 'en' ? 'zh' : 'en');
document.addEventListener('keydown', event => {
  if (event.key === 'ArrowLeft') document.getElementById('prev').click();
  if (event.key === 'ArrowRight') document.getElementById('next').click();
});
applyLanguage(language);
setView(mode, allEvents[allEvents.length - 1]?.step);
</script>
</body>
</html>
'''


def write_report(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = dict(payload)
    document["translations"] = _REPORT_MESSAGES
    encoded = json.dumps(document, ensure_ascii=False).replace("</", "<\\/")
    output_path.write_text(HTML_TEMPLATE.replace("__DATA__", encoded), encoding="utf-8")
