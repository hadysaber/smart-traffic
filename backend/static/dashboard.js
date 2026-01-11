const statusUrl = "/api/status";
const countsUrl = "/api/process_counts";

const elements = {
  countN: document.getElementById("count-n"),
  countE: document.getElementById("count-e"),
  countS: document.getElementById("count-s"),
  countW: document.getElementById("count-w"),
  totalNS: document.getElementById("total-ns"),
  totalEW: document.getElementById("total-ew"),
  totalAll: document.getElementById("total-all"),
  nsGreen: document.getElementById("ns-green"),
  ewGreen: document.getElementById("ew-green"),
  cycle: document.getElementById("cycle"),
  currentPhase: document.getElementById("current-phase"),
  cvStatus: document.getElementById("cv-status"),
  mlStatus: document.getElementById("ml-status"),
  camStatus: document.getElementById("cam-status"),
  lightsStatus: document.getElementById("lights-status"),
  lastUpdate: document.getElementById("last-update"),
};

const patterns = {
  "balanced": [6, 6, 6, 6],
  "ns-heavy": [14, 3, 12, 3],
  "ew-heavy": [3, 12, 3, 14],
};

function setIndicator(element, isActive) {
  element.classList.toggle("active", Boolean(isActive));
}

function updateCounts(counts) {
  if (!Array.isArray(counts) || counts.length !== 4) {
    return;
  }
  const [n, e, s, w] = counts;
  elements.countN.textContent = n;
  elements.countE.textContent = e;
  elements.countS.textContent = s;
  elements.countW.textContent = w;
  const nsTotal = n + s;
  const ewTotal = e + w;
  elements.totalNS.textContent = nsTotal;
  elements.totalEW.textContent = ewTotal;
  elements.totalAll.textContent = nsTotal + ewTotal;
}

function updateTimings(timings) {
  if (!timings || !timings.predictions) {
    elements.nsGreen.textContent = "--";
    elements.ewGreen.textContent = "--";
    elements.cycle.textContent = "--";
    return;
  }
  elements.nsGreen.textContent = `${timings.predictions.ns_green}s`;
  elements.ewGreen.textContent = `${timings.predictions.ew_green}s`;
  elements.cycle.textContent = `${timings.predictions.total_cycle}s`;
}

function updatePhase(timings) {
  if (!timings || !timings.commands) {
    elements.currentPhase.textContent = "--";
    return;
  }
  const phase1 = timings.commands.phase1;
  if (phase1 && phase1.description) {
    elements.currentPhase.textContent = phase1.description;
    return;
  }
  elements.currentPhase.textContent = "Awaiting phase";
}

function updateStatus(data) {
  updateCounts(data.last_counts);
  updateTimings(data.last_timings);
  updatePhase(data.last_timings);

  setIndicator(elements.cvStatus, true);
  setIndicator(elements.mlStatus, Boolean(data.last_timings));
  setIndicator(elements.camStatus, data.esp32_camera_connected);
  setIndicator(elements.lightsStatus, data.esp32_lights_connected);

  elements.lastUpdate.textContent = data.last_update_timestamp || "--";
}

async function fetchStatus() {
  try {
    const response = await fetch(statusUrl, { cache: "no-store" });
    if (!response.ok) {
      throw new Error("Failed to fetch status");
    }
    const data = await response.json();
    updateStatus(data);
  } catch (error) {
    console.error(error);
  }
}

async function sendPattern(patternKey) {
  const counts = patterns[patternKey];
  if (!counts) {
    return;
  }
  try {
    const response = await fetch(countsUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ car_counts: counts }),
    });
    if (!response.ok) {
      throw new Error("Failed to send counts");
    }
    const data = await response.json();
    updateStatus({
      last_counts: data.counts,
      last_timings: data.timings,
      last_update_timestamp: new Date().toISOString(),
      esp32_camera_connected: false,
      esp32_lights_connected: false,
    });
  } catch (error) {
    console.error(error);
  }
}

document.querySelectorAll(".btn").forEach((button) => {
  button.addEventListener("click", () => {
    sendPattern(button.dataset.pattern);
  });
});

fetchStatus();
setInterval(fetchStatus, 1000);
