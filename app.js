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

// --- SSE client: listen to backend event stream and trigger UI ---
(function setupSSE(){
  const url = 'http://localhost:8080/api/stream';
  let retry = 1000;

  function connect() {
    const es = new EventSource(url);

    es.onopen = () => {
      console.log('SSE connected');
      retry = 1000;
      const statusText = document.getElementById('status-text');
      if (statusText) statusText.textContent = 'Connected';
    };

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        const type = data.type;
        // Map backend event types to frontend alert ids
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
    };

    es.onerror = () => {
      console.warn('SSE error — attempting reconnect');
      const statusText = document.getElementById('status-text');
      if (statusText) statusText.textContent = 'Disconnected';
      try { es.close(); } catch(_) {}
      setTimeout(() => {
        retry = Math.min(30000, retry * 2);
        connect();
      }, retry);
    };
  }

  connect();
})();