const SOUNDS = [
  {
    id: "siren",
    name: "Emergency Siren",
    desc: "Police / Ambulance / Fire truck",
    icon: "🚨",
    defaultColor: "#ff3a3a",
    colors: ["#ff3a3a","#ff1493","#e040fb","#ff5722"]
  },
  {
    id: "fire",
    name: "Fire Alarm",
    desc: "Building fire alarm / smoke detector",
    icon: "🔥",
    defaultColor: "#ff6b2b",
    colors: ["#ff6b2b","#ff4500","#ff7043","#ef5350"]
  }
];

let state = {
  enabled: { siren: true, fire: true },
  selectedColor: { siren: "#ff3a3a", fire: "#ff6b2b" },
  log: [],
  currentAlert: null
};

let flashTimeout = null;
let alertTimeout = null;

function fireAlert(id) {
  const sound = SOUNDS.find(s => s.id === id);
  if (!sound) return;

  const color = state.selectedColor[id];

  // Cancel any running alert
  clearTimeout(flashTimeout);
  clearTimeout(alertTimeout);

  state.currentAlert = id;

  // 1. Flash overlay
  const overlay = document.getElementById("flash-overlay");
  overlay.style.background = color;
  overlay.classList.add("active");

  // 2. Banner
  const banner = document.getElementById("alert-banner");
  banner.style.background = color;
  document.getElementById("banner-icon").textContent = sound.icon;
  document.getElementById("banner-text").textContent = `${sound.name.toUpperCase()} DETECTED`;
  banner.classList.add("active");

  // 3. Icon ring
  const ring = document.getElementById("icon-ring");
  ring.className = "icon-ring alert alert-" + id;
  ring.style.borderColor = color;
  ring.style.color = color;
  ring.style.background = color + "12";
  ring.style.boxShadow = `0 0 70px ${color}30`;
  document.getElementById("icon-inner").textContent = sound.icon;

  // Force re-trigger ring pulse animation
  void ring.offsetWidth;
  ring.classList.add("alert");

  // 4. Label
  const label = document.getElementById("detection-label");
  label.className = "detection-label " + id;
  label.style.color = color;
  label.textContent = sound.name;


  // Second flash pulse
  flashTimeout = setTimeout(() => {
    overlay.classList.remove("active");
    setTimeout(() => {
      overlay.classList.add("active");
      setTimeout(() => overlay.classList.remove("active"), 160);
    }, 100);
  }, 180);

  // Auto-clear after 3.5s
  alertTimeout = setTimeout(() => clearAlert(), 3500);
}

function clearAlert() {
  state.currentAlert = null;
  document.getElementById("flash-overlay").classList.remove("active");
  document.getElementById("alert-banner").classList.remove("active");

  const ring = document.getElementById("icon-ring");
  ring.className = "icon-ring";
  ring.style.borderColor = "";
  ring.style.color = "";
  ring.style.background = "";
  ring.style.boxShadow = "";
  document.getElementById("icon-inner").textContent = "👂";

  const label = document.getElementById("detection-label");
  label.className = "detection-label";
  label.style.color = "";
  label.textContent = "Awaiting Sound…";
}

// --- SSE manager: start/stop live connection and map events to UI ---
const SSEManager = (function(){
  const url = 'http://localhost:8080/api/stream';
  let es = null;
  let isRunning = false;
  let retry = 1000;
  let reconnectTimer = null;

  function setStatus(text, on) {
    const statusText = document.getElementById('status-text');
    if (statusText) statusText.textContent = text;
    const badge = document.getElementById('status-badge');
    if (badge) {
      badge.classList.toggle('on', !!on);
      badge.classList.toggle('off', !on);
    }
  }

  function handleMessage(e) {
    try {
      const data = JSON.parse(e.data);
      const type = data.type;
      if (type === 'SIREN_ALARM') {
        if (state.enabled.siren) fireAlert('siren');
      } else if (type === 'FIRE_ALARM') {
        if (state.enabled.fire) fireAlert('fire');
      } else if (type === 'IDLE' || type === 'HOME') {
        clearAlert();
      }
    } catch (err) {
      console.warn('Failed parsing SSE message', err, e.data);
    }
  }

  function connect() {
    if (!isRunning) return;
    try {
      es = new EventSource(url);
    } catch (err) {
      scheduleReconnect();
      return;
    }

    es.onopen = () => {
      console.log('SSE connected');
      retry = 1000;
      setStatus('Connected', true);
    };

    es.onmessage = handleMessage;

    es.onerror = () => {
      console.warn('SSE error — attempting reconnect');
      setStatus('Disconnected', false);
      try { es.close(); } catch(_) {}
      es = null;
      scheduleReconnect();
    };
  }

  function scheduleReconnect() {
    if (!isRunning) return;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(() => {
      retry = Math.min(30000, retry * 2);
      connect();
    }, retry);
  }

  function start() {
    if (isRunning) return;
    isRunning = true;
    retry = 1000;
    setStatus('Connecting…', true);
    connect();
  }

  function stop() {
    if (!isRunning) return;
    isRunning = false;
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
    if (es) try { es.close(); } catch(_) {}
    es = null;
    setStatus('Stopped', false);
    clearAlert();
  }

  return { start, stop, get running(){ return isRunning; } };
})();

// Wire the toggle button
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('toggle-btn');
  if (!btn) return;
  btn.addEventListener('click', () => {
    if (SSEManager.running) {
      SSEManager.stop();
      btn.textContent = 'Start';
      btn.classList.remove('running');
    } else {
      SSEManager.start();
      btn.textContent = 'Stop';
      btn.classList.add('running');
    }
  });
});