// --- Chart.js Minimalist Defaults (Government Theme) ---
Chart.defaults.color = '#1d1b1a'; // Dark text for white background
Chart.defaults.borderColor = '#b1b4b6';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.plugins.legend.display = false;

const chartScaleOpts = {
  grid: { color: '#e5e7eb', drawBorder: false },
  ticks: { font: { size: 11 } }
};

// Resolve API root intelligently:
// - If frontend is served from an HTTP origin, use same-origin `/api`.
// - If opened via file:// or running on a different host, default to localhost:8000 (demo server).
let API_ROOT = '/api'
try {
  const origin = window.location && window.location.origin ? window.location.origin : ''
  if (!origin || origin === 'null') {
    API_ROOT = 'http://127.0.0.1:8000/api'
  } else {
    // Use same origin by default, but if origin is not localhost and you want local demo API,
    // set window.FIRE_MAMBA_API manually before loading app.js
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      // keep relative /api for production
    } else {
      // for local development if needed, but relative usually works
    }
  }
} catch (e) {
  API_ROOT = 'http://127.0.0.1:8000/api'
}

async function fetchJson(path) {
  const res = await fetch(path)
  return res.json()
}

// --- Chart Initializations ---

// Initialize Fused Score Chart
const ctx = document.getElementById('fusedChart').getContext('2d')
const fusedChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      label: 'Fused Score',
      data: [],
      borderColor: '#005ea2',
      backgroundColor: 'rgba(0, 94, 162, 0.2)', // More visible fill
      fill: true,
      tension: 0.4,
      borderWidth: 3,
      pointRadius: 0, // Clean look, points on hover only
      pointHoverRadius: 6
    }]
  },
  options: { scales: { y: { min: 0, max: 1, ...chartScaleOpts }, x: { display: false } } }
})

const ctxTemp = document.getElementById('tempChart').getContext('2d')
const tempChart = new Chart(ctxTemp, {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      { label: 'Temp (°C)', data: [], borderColor: '#ff3535', backgroundColor: 'rgba(255, 53, 53, 0.1)', fill: true, tension: 0.4, borderWidth: 3, yAxisID: 'y' },
      { label: 'Env Risk', data: [], borderColor: '#ffa500', borderDash: [5, 5], tension: 0.4, borderWidth: 2, yAxisID: 'y1' }
    ]
  },
  options: {
    interaction: { mode: 'index', intersect: false },
    scales: {
      y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Temp' }, ...chartScaleOpts },
      y1: { type: 'linear', display: true, position: 'right', min: 0, max: 1, grid: { drawOnChartArea: false }, title: { display: true, text: 'Risk' }, ...chartScaleOpts },
      x: { display: false }
    }
  }
})

const ctxChem = document.getElementById('chemVisChart').getContext('2d')
const chemVisChart = new Chart(ctxChem, {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      { label: 'Chemical (VOC)', data: [], borderColor: '#35b8ff', backgroundColor: 'rgba(53, 184, 255, 0.1)', fill: true, tension: 0.4, borderWidth: 3 },
      { label: 'Visual (Smoke)', data: [], borderColor: '#9b35ff', backgroundColor: 'rgba(155, 53, 255, 0.1)', fill: true, tension: 0.4, borderWidth: 3 }
    ]
  },
  options: { scales: { y: { min: 0, max: 1, ...chartScaleOpts }, x: { display: false } } }
})

const ctxHurst = document.getElementById('hurstChart').getContext('2d')
const hurstChart = new Chart(ctxHurst, {
  type: 'line',
  data: {
    labels: [],
    datasets: [{ label: 'Hurst (H)', data: [], borderColor: '#00e0df', backgroundColor: 'rgba(0,224,223,0.1)', tension: 0.1 }]
  },
  options: {
    scales: { y: { min: 0, max: 1, ...chartScaleOpts }, x: { display: false } },
    plugins: { annotation: { annotations: { line1: { type: 'line', yMin: 0.5, yMax: 0.5, borderColor: '#666', borderWidth: 1, borderDash: [5, 5] } } } }
  }
})

const ctxLyap = document.getElementById('lyapunovChart').getContext('2d')
const lyapunovChart = new Chart(ctxLyap, {
  type: 'line',
  data: {
    labels: [],
    datasets: [{ label: 'Lyapunov (λ)', data: [], borderColor: '#ff00ff', backgroundColor: 'rgba(255,0,255,0.1)', tension: 0.1 }]
  },
  options: { scales: { y: { recommendedMin: -1, recommendedMax: 1, ...chartScaleOpts }, x: { display: false } } }
})

// --- UI Descriptions & Updates ---

function updateThreatBadge(riskScore) {
  const badge = document.getElementById('threatBadge');
  if (riskScore > 0.8) {
    badge.style.background = '#d4351c'; // Danger
    badge.textContent = 'CRITICAL ALERT';
  } else if (riskScore > 0.5) {
    badge.style.background = '#f47738'; // Warning
    badge.textContent = 'ELEVATED RISK';
  } else {
    badge.style.background = '#00703c'; // Normal
    badge.textContent = 'NORMAL OPERATIONS';
  }
}

function updateNodeInfo(data) {
  // Update Threat Badge based on Fused Score
  if (data.mamba_ssm && data.mamba_ssm.fused_score !== undefined) {
    updateThreatBadge(data.mamba_ssm.fused_score);
    document.getElementById('mambaScoreVal').textContent = data.mamba_ssm.fused_score.toFixed(2);
    document.getElementById('temporalConf').textContent = (data.mamba_ssm.temporal_confidence * 100).toFixed(0) + '%';
  }

  if (data.node_id) {
    // document.getElementById('nodeId').textContent = data.node_id; // element removed in gov theme
  }

  document.getElementById('riskTier').textContent = data.risk_tier;

  // Map 'visual_score' from backend to Visual Confidence display
  if (data.vision) {
    document.getElementById('visualConfVal').textContent = (data.vision.visual_score || 0).toFixed(2);
    document.getElementById('visionMode').textContent = data.vision.vision_mode;
    document.getElementById('cameraHealth').textContent = data.vision.camera_health ? data.vision.camera_health.health_score : '--';
  }

  // NEW: System Status & Weights
  if (data.system_status) {
    document.getElementById('activePhase').textContent = data.system_status.phase
    document.getElementById('finalRiskDisplay').textContent = data.system_status.final_risk.toFixed(2)

    const w = data.system_status.weights
    // Update widths for analysis weights bars
    if (w) {
      document.getElementById('wVisBar').style.width = w.visual + '%'
      document.getElementById('wThermBar').style.width = w.thermal + '%'
      document.getElementById('wChemBar').style.width = w.chemical + '%'
    }

    // Color code risk number locally
    const riskEl = document.getElementById('finalRiskDisplay')
    if (data.system_status.final_risk > 0.8) riskEl.style.color = '#d4351c'
    else if (data.system_status.final_risk > 0.5) riskEl.style.color = '#f47738'
    else riskEl.style.color = '#0b0c0c' // Default text color
  }

  // Fractal Gate (Phase-2)
  if (data.fractal) {
    const h = data.fractal.hurst || 0.5
    document.getElementById('hurstVal').textContent = h.toFixed(2)
    document.getElementById('hurstBar').style.width = Math.min(100, (h / 1.0) * 100) + '%' // Hurst is 0-1
    document.getElementById('fractalStatus').textContent = data.fractal.status || 'WAITING'
    document.getElementById('fractalStatus').style.color = data.fractal.has_structure ? '#d4351c' : '#00703c'
  }

  // Chaos Kernel (Phase-3)
  if (data.chaos) {
    const ly = data.chaos.lyapunov || 0.0
    document.getElementById('lyapVal').textContent = ly.toFixed(2)
    // Visualize lyapunov: range typically -1 to 1. Map -1..1 to 0..100%
    const lyPct = Math.min(100, Math.max(0, (ly + 1) * 50))
    document.getElementById('lyapBar').style.width = lyPct + '%'
    document.getElementById('chaosStatus').textContent = data.chaos.status || 'WAITING'
    document.getElementById('chaosStatus').style.color = data.chaos.is_unstable ? '#d4351c' : '#00703c'
  }

  // Component Breakdown
  const c = data.components || {}
  document.getElementById('scoreChem').textContent = (c.chemical || 0).toFixed(2)
  document.getElementById('barChem').style.width = ((c.chemical || 0) * 100) + '%'

  document.getElementById('scoreVis').textContent = (c.visual || 0).toFixed(2)
  document.getElementById('barVis').style.width = ((c.visual || 0) * 100) + '%'

  document.getElementById('scoreEnv').textContent = (c.environmental || 0).toFixed(2)
  document.getElementById('barEnv').style.width = ((c.environmental || 0) * 100) + '%'
}

// Map Logic
let map = null;
let nodeMarker = null;
let detectionMarkers = {};

function initMap() {
  // Default to Australia
  map = L.map('map').setView([-35.714, 150.179], 13);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);
}

function updateNodeMarker(loc, tier) {
  if (!map) initMap();

  const lat = loc.latitude;
  const lng = loc.longitude;
  const color = tier === 'CRITICAL' ? '#d4351c' : tier === 'ELEVATED' ? '#f47738' : '#00703c';

  if (nodeMarker) {
    nodeMarker.setLatLng([lat, lng]);
    nodeMarker.setStyle({ color: color, fillColor: color });
  } else {
    nodeMarker = L.circleMarker([lat, lng], {
      radius: 8,
      color: color,
      fillColor: color,
      fillOpacity: 0.8
    }).addTo(map);
    map.setView([lat, lng], 13);
  }
}

function zoomToAlert(alert, opts = { zoom: 16 }) {
  if (!map) return;
  if (alert.location) {
    map.setView([alert.location.latitude, alert.location.longitude], opts.zoom);
    L.popup()
      .setLatLng([alert.location.latitude, alert.location.longitude])
      .setContent(`<strong>${alert.level} ALERT</strong><br>${new Date(alert.timestamp).toLocaleTimeString()}`)
      .openOn(map);
  }
}

// --- Data Loading & Logic ---

async function loadHistory() {
  try {
    const h = await fetchJson(API_ROOT + '/history')
    const labels = h.series.map(p => new Date(p.timestamp).toLocaleTimeString())

    // Fused Score
    fusedChart.data.labels = labels
    fusedChart.data.datasets[0].data = h.series.map(p => p.fused_score)
    fusedChart.update()

    // Temp & Env
    tempChart.data.labels = labels
    tempChart.data.datasets[0].data = h.series.map(p => p.temp || 0)
    tempChart.data.datasets[1].data = h.series.map(p => p.env_score || 0)
    tempChart.update()

    // Chem & Visual
    chemVisChart.data.labels = labels
    chemVisChart.data.datasets[0].data = h.series.map(p => p.chemical || 0)
    chemVisChart.data.datasets[1].data = h.series.map(p => p.visual || 0)
    chemVisChart.update()

    // Fractal (Hurst)
    hurstChart.data.labels = labels
    hurstChart.data.datasets[0].data = h.series.map(p => p.hurst || 0.5)
    hurstChart.update()

    // Chaos (Lyapunov)
    lyapunovChart.data.labels = labels
    lyapunovChart.data.datasets[0].data = h.series.map(p => p.lyapunov || 0)
    lyapunovChart.update()

    // update alerts derived from history (local heuristics)
    const localAlerts = findAlertsFromSeries(h.series)
    renderAlerts(localAlerts)
  } catch (e) {
    console.warn("History load failed", e);
  }
}

async function loadStatus() {
  try {
    const s = await fetchJson(API_ROOT + '/status')
    updateNodeInfo(s)

    // Update map if location is present
    if (s.location && s.location.latitude) {
      updateNodeMarker(s.location, s.risk_tier)
    }

    // fetch persisted alerts
    const allAlertsResp = await fetchJson(API_ROOT + '/alerts')
    const allAlerts = allAlertsResp.alerts || []
    // per-node alerts logic could go here
  } catch (e) {
    console.warn("Status load failed", e);
  }
}

// Detections layer (UAV detections)
async function loadDetections() {
  try {
    const r = await fetchJson(API_ROOT + '/detections')
    const dets = r.detections || []

    const feedImg = document.getElementById('cameraFeed')
    const feedPlaceholder = document.getElementById('cameraPlaceholder')
    const camStatus = document.getElementById('camStatus')

    if (dets.length > 0) {
      const latest = dets[0]
      let src = ''
      if (latest.image_url) src = latest.image_url
      else if (latest.image_b64) src = `data:image/jpeg;base64,${latest.image_b64}`

      if (src) {
        feedImg.src = src
        feedImg.style.display = 'block'
        feedPlaceholder.style.display = 'none'
        camStatus.textContent = 'DETECTING'
        camStatus.style.color = '#d4351c'
      }
    } else {
      // If needed, reset or show placeholder
    }
  } catch (e) {
    console.error('failed to load detections', e)
  }
}

function findAlertsFromSeries(series) {
  const alerts = []
  series.forEach(pt => {
    const score = pt.fused_score
    if (score >= 0.8) alerts.push({ level: 'RED', score, ts: pt.timestamp })
    else if (score >= 0.6) alerts.push({ level: 'ORANGE', score, ts: pt.timestamp })
  })
  return alerts.slice(-20).reverse() // Show last 20 alerts instead of 5
}

function renderAlerts(alerts) {
  const container = document.getElementById('alertsList')
  container.innerHTML = ''
  if (!alerts || alerts.length === 0) {
    container.innerHTML = '<p style="color:var(--text-secondary)">No alerts recently</p>'
    return
  }
  const ul = document.createElement('ul')
  ul.style.listStyle = 'none';
  ul.style.padding = 0;

  alerts.forEach(a => {
    const li = document.createElement('li')
    li.style.padding = '8px';
    li.style.borderBottom = '1px solid #eee';
    const time = a.ts ? new Date(a.ts).toLocaleTimeString() : ''
    const color = a.level === 'RED' ? '#d4351c' : '#f47738';
    li.innerHTML = `<strong style="color:${color}">${a.level}</strong> <span style="color:#505a5f; font-size:0.9em;">(${time})</span> Score: ${a.score.toFixed(2)}`
    ul.appendChild(li)
  })
  container.appendChild(ul)
}

function downloadCSV(series) {
  const rows = [['timestamp', 'fused_score', 'temp', 'env_risk', 'chemical', 'visual', 'fractal_hurst', 'chaos_lyapunov']]
  series.forEach(p => rows.push([
    p.timestamp,
    p.fused_score,
    p.temp || 0,
    p.env_score || 0,
    p.chemical || 0,
    p.visual || 0,
    p.hurst || 0.5,
    p.lyapunov || 0
  ]))
  const csv = rows.map(r => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `fractal_fire_history_${Date.now()}.csv`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

// Focus the latest global RED alert
async function focusLatestRed() {
  try {
    const all = await fetchJson(API_ROOT + '/alerts')
    const alerts = all.alerts || []
    // find most recent RED
    const redAlerts = alerts.filter(a => a.level === 'RED' && a.location)
    if (redAlerts.length === 0) {
      alert('No RED alerts with location available')
      return
    }
    // assume alerts are sorted desc by timestamp from server; otherwise sort
    redAlerts.sort((a, b) => (a.timestamp < b.timestamp) ? 1 : -1)
    zoomToAlert(redAlerts[0], { zoom: 16 })
  } catch (e) {
    console.error("Focus alert failed", e);
  }
}

async function refreshAll() {
  await loadHistory()
  await loadStatus()
  await loadDetections()
  if (!map) initMap(); // Ensure map inits
}

window.addEventListener('load', () => {
  initMap();
  refreshAll()

  const btnCsv = document.getElementById('downloadCsv');
  if (btnCsv) {
    btnCsv.addEventListener('click', async () => {
      const h = await fetchJson(API_ROOT + '/history')
      if (h && h.series) downloadCSV(h.series);
    })
  }

  const btnFocus = document.getElementById('focusLatestRed');
  if (btnFocus) {
    btnFocus.addEventListener('click', () => {
      focusLatestRed();
    });
  }

  // Refresh every 5s
  setInterval(refreshAll, 5000)
})