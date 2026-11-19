// Robot cockpit page: state from /events (Server-Sent Events), video from /stream.mjpg.
'use strict';

const RETRY_MS = 1000;      // wait before the video reconnects
const STALE_MS = 1500;      // no state for this long: the link counts as stale
const LOW_BATTERY_V = 11.4; // CLAUDE.md: do not drive below
const HISTORY_LEN = 8;      // states shown in the history row
const FLASH_MS = 1000;
const COLOR = { green: '#2ecc71', yellow: '#f1c40f', orange: '#e67e22', red: '#e74c3c', gray: '#7f8c8d' };
const STATE_COLOR = {
  IDLE: COLOR.gray, ROAD_FOLLOWING: COLOR.green, SLOW_DOWN: COLOR.yellow, STOP: COLOR.yellow,
  OBSTACLE_AVOIDANCE: COLOR.orange, ROAD_RECOVERY: COLOR.orange, LINE_RECOVERY: COLOR.orange, HALT: COLOR.red,
};

// State machine drawing (viewBox 720 x 420): state: [label, centre x, centre y]; edges as in STATE_MACHINE.md,
// for the runs the cockpit starts (adaptive, with LINE_RECOVERY)
const NODE_W = 110, NODE_H = 44, PAIR_GAP = 6;
const NODES = {
  STOP: ['STOP', 70, 70], SLOW_DOWN: ['SLOW', 250, 70],
  IDLE: ['IDLE', 70, 200], ROAD_FOLLOWING: ['FOLLOW', 250, 200], OBSTACLE_AVOIDANCE: ['AVOID', 430, 200],
  HALT: ['HALT', 630, 200], LINE_RECOVERY: ['LINE REC', 250, 330], ROAD_RECOVERY: ['ROAD REC', 430, 330],
};
// [from, to, control point of a curved edge (optional)]
const EDGES = [
  ['IDLE', 'ROAD_FOLLOWING'], ['ROAD_FOLLOWING', 'SLOW_DOWN'], ['SLOW_DOWN', 'ROAD_FOLLOWING'],
  ['ROAD_FOLLOWING', 'STOP'], ['SLOW_DOWN', 'STOP'], ['STOP', 'ROAD_FOLLOWING'],
  ['ROAD_FOLLOWING', 'OBSTACLE_AVOIDANCE'], ['SLOW_DOWN', 'OBSTACLE_AVOIDANCE'],
  ['OBSTACLE_AVOIDANCE', 'ROAD_RECOVERY'], ['ROAD_RECOVERY', 'OBSTACLE_AVOIDANCE'],
  ['ROAD_RECOVERY', 'ROAD_FOLLOWING'], ['ROAD_RECOVERY', 'LINE_RECOVERY'],
  ['OBSTACLE_AVOIDANCE', 'LINE_RECOVERY'], ['ROAD_FOLLOWING', 'LINE_RECOVERY'], ['LINE_RECOVERY', 'ROAD_FOLLOWING'],
  ['SLOW_DOWN', 'LINE_RECOVERY', { x: 110, y: 200 }],
  ['OBSTACLE_AVOIDANCE', 'HALT'], ['LINE_RECOVERY', 'HALT'],  // FOLLOW -> HALT only in baseline runs
  ['HALT', 'IDLE', { x: 350, y: 560 }],
];

const $ = (id) => document.getElementById(id);
const put = (id, text) => { $(id).textContent = text; };
const fmt = (v, digits = 2) => (typeof v === 'number' && isFinite(v) ? v.toFixed(digits) : '-');
const yesNo = (v) => (v == null ? '-' : v ? 'yes' : 'no');
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

const stateLog = [];  // {state, t}: the last states and when they were entered
let lastState = null;
let lastMessage = 0;
let driving = false;
let wasDown = false;  // the link was lost: reload the video once it is back

// --- bars ---
function setSigned(id, v) {  // fill grows from the centre toward v (-1..1)
  const x = typeof v === 'number' ? clamp(v, -1, 1) : 0;
  $(id).style.left = (x < 0 ? 50 + x * 50 : 50) + '%';
  $(id).style.width = Math.abs(x) * 50 + '%';
}
function setUnsigned(id, v) {  // 0..1
  $(id).style.width = (typeof v === 'number' ? clamp(v, 0, 1) : 0) * 100 + '%';
}
function setLaneX(v) {
  $('lane-x').style.display = typeof v === 'number' ? '' : 'none';
  $('lane-x').style.left = (clamp(v ?? 0, -1, 1) + 1) * 50 + '%';
}

// --- state machine ---
const centre = (name) => ({ x: NODES[name][1], y: NODES[name][2] });

function boxEdge(a, b) {  // where the line from centre a toward point b leaves a's box
  const dx = b.x - a.x, dy = b.y - a.y;
  const s = Math.min(dx ? NODE_W / 2 / Math.abs(dx) : Infinity, dy ? NODE_H / 2 / Math.abs(dy) : Infinity);
  return { x: a.x + dx * s, y: a.y + dy * s };
}

function edgePath(from, to, ctrl) {
  const a = centre(from), b = centre(to);
  if (ctrl) {
    const p = boxEdge(a, ctrl), q = boxEdge(b, ctrl);
    return `M${p.x},${p.y} Q${ctrl.x},${ctrl.y} ${q.x},${q.y}`;
  }
  const len = Math.hypot(b.x - a.x, b.y - a.y);  // shift sideways so A->B and B->A do not overlap
  const nx = -(b.y - a.y) / len * PAIR_GAP, ny = (b.x - a.x) / len * PAIR_GAP;
  const p = boxEdge(a, b), q = boxEdge(b, a);
  return `M${p.x + nx},${p.y + ny} L${q.x + nx},${q.y + ny}`;
}

function drawStateMachine() {
  const arrow = '<marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" ' +
                'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#5a6372"/></marker>';
  const edges = EDGES.map(([a, b, ctrl]) =>
    `<path id="e-${a}-${b}" class="edge" marker-end="url(#arrow)" d="${edgePath(a, b, ctrl)}"/>`).join('');
  const nodes = Object.entries(NODES).map(([name, [label, x, y]]) =>
    `<g id="n-${name}" class="node" style="color:${STATE_COLOR[name]}" ` +
    `transform="translate(${x - NODE_W / 2},${y - NODE_H / 2})"><title>${name}</title>` +
    `<rect width="${NODE_W}" height="${NODE_H}" rx="10"/><text x="${NODE_W / 2}" y="${NODE_H / 2}">${label}</text></g>`
  ).join('');
  $('sm').innerHTML = `<defs>${arrow}</defs>${edges}${nodes}`;
}

function flashEdge(from, to) {
  const el = $(`e-${from}-${to}`);
  if (!el) return;  // a run that ended by time or by hand: no drawn edge
  el.style.stroke = STATE_COLOR[to];
  el.classList.remove('flash');
  void el.getBoundingClientRect();  // restart the animation
  el.classList.add('flash');
  setTimeout(() => { el.classList.remove('flash'); el.style.stroke = ''; }, FLASH_MS);
}

function renderHistory() {
  const now = Date.now();
  $('hist').innerHTML = stateLog.map((h, i) => {
    const end = i + 1 < stateLog.length ? stateLog[i + 1].t : now;
    return `<span class="chip" style="background:${STATE_COLOR[h.state]}">${NODES[h.state][0]} ` +
           `${((end - h.t) / 1000).toFixed(1)}s</span>`;
  }).join('');
}

function updateStateMachine(name) {
  const known = name in NODES;
  if (known && name !== lastState) {
    if (lastState) flashEdge(lastState, name);
    stateLog.push({ state: name, t: Date.now() });
    if (stateLog.length > HISTORY_LEN) stateLog.shift();
    lastState = name;
  }
  for (const n of Object.keys(NODES)) $('n-' + n).classList.toggle('on', known && n === name);
}

// --- one state ---
function render(s) {
  const v = s.values || {};
  const name = v.mode || s.mode || '-';
  driving = s.mode === 'DRIVING';
  $('badge').textContent = name;
  $('badge').style.background = STATE_COLOR[name] || COLOR.gray;
  updateStateMachine(name);
  put('phase', v.phase || (driving ? '' : 'motors off'));
  $('start').disabled = driving;

  put('battery', typeof v.battery_v === 'number'
    ? `${v.battery_v.toFixed(2)} V  ${s.battery_pct == null ? '-' : Math.round(s.battery_pct)} %` : '-');
  $('battery').classList.toggle('low', typeof v.battery_v === 'number' && v.battery_v < LOW_BATTERY_V);

  for (const key of ['left', 'right', 'speed', 'steering']) {
    setSigned(key, v[key]);
    put(key + '-v', fmt(v[key]));
  }
  setUnsigned('lane-vis', v.lane_visible);
  put('lane-vis-v', fmt(v.lane_visible));
  setLaneX(v.lane_x);
  put('lane-x-v', fmt(v.lane_x));

  put('direction', v.direction || '-');
  put('pass-side', v.pass_side || '-');
  put('curve-class', v.curve_class ?? '-');
  put('curve-dir', fmt(v.curve_dir));
  put('probs', `${fmt(v.p_straight)} / ${fmt(v.p_gentle)} / ${fmt(v.p_sharp)}`);
  put('lane-aligned', yesNo(v.lane_aligned));
  put('cup-visible', fmt(v.cup_visible));
  put('band-cm', fmt(v.band_cm, 1));

  put('time', fmt(v.time, 1));
  put('hz', v.dt > 0 ? fmt(1 / v.dt, 1) : '-');
  put('fps', fmt(s.fps, 1));
  put('stream-fps', `${fmt(s.stream_fps, 1)} / ${fmt(s.overlay_fps, 1)}`);
  put('cam-fps', `${fmt($('overlay').checked ? s.overlay_fps : s.stream_fps, 0)} fps`);
  put('inference', fmt(v.inference_ms, 1));
  put('reason', 'last run: ' + (s.last_reason ?? '-'));
}

// --- link: connected / stale / down ---
function setLink(kind, text) {
  $('conn-dot').className = 'dot ' + kind;
  put('conn', text);
}

function watchLink() {
  const age = Date.now() - lastMessage;
  put('age', lastMessage ? String(age) : '-');
  if (lastMessage && age > STALE_MS && $('conn-dot').classList.contains('live')) setLink('stale', 'no new state');
  renderHistory();
}

let events = null;

function connectEvents() {
  events = new EventSource('/events');
  events.onopen = () => {
    setLink('live', 'live');
    if (wasDown) setStream();
    wasDown = false;
  };
  events.onmessage = (e) => {
    lastMessage = Date.now();
    if (!$('conn-dot').classList.contains('live')) setLink('live', 'live');
    render(JSON.parse(e.data));
  };
  events.onerror = () => {  // EventSource reconnects by itself
    wasDown = true;
    setLink('down', 'disconnected, retrying');
  };
}

// --- video and buttons ---
function setStream() {
  $('cam').src = `/stream.mjpg?overlay=${$('overlay').checked ? 1 : 0}&t=${Date.now()}`;
}

async function send(path, body) {
  try {
    const res = await fetch(path, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    const answer = await res.json().catch(() => ({}));
    put('status', res.ok ? `${path.slice(1)}: ok` : `${path.slice(1)}: ${answer.error || 'HTTP ' + res.status}`);
  } catch (e) {
    put('status', `${path.slice(1)}: failed (${e.message})`);
  }
}

const stop = () => send('/stop');

$('cam').onerror = () => { if (!document.hidden) setTimeout(setStream, RETRY_MS); };
$('overlay').onchange = setStream;
$('start').onclick = () => send('/start', { mode: $('mode').value, seconds: Number($('seconds').value) });
$('stop').onclick = stop;
document.addEventListener('keydown', (e) => {  // Esc always stops; Space stops unless typing in a field
  const typing = ['INPUT', 'SELECT'].includes(document.activeElement.tagName);
  if (e.key === 'Escape' || (e.key === ' ' && !typing)) {
    e.preventDefault();
    stop();
  }
});

// a hidden tab closes its two long connections: the browser allows few per host, and STOP must get through
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    events.close();
    $('cam').removeAttribute('src');
    setLink('down', 'paused (tab hidden)');
  } else {
    connectEvents();
    setStream();
  }
});

drawStateMachine();
setStream();
connectEvents();
setInterval(watchLink, 250);
