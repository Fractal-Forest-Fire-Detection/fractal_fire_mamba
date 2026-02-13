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
    const mambaEl = document.getElementById('mambaScoreVal');
    if (mambaEl) mambaEl.textContent = data.mamba_ssm.fused_score.toFixed(2);
    const confEl = document.getElementById('temporalConf');
    if (confEl) confEl.textContent = (data.mamba_ssm.temporal_confidence * 100).toFixed(0) + '%';
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

// ==========================================================================
// THE HIVE: Multi-Queen Mesh Network + Map Markers
// ==========================================================================

let meshAnimFrame = 0;
let lastMeshData = null;
let meshMarkers = [];  // Leaflet markers for nodes
let meshLines = [];    // Leaflet polylines for LoRa links
let dropdownPopulated = false;

async function loadMesh() {
  try {
    const mesh = await fetchJson(API_ROOT + '/mesh')
    if (!mesh || !mesh.nodes) return;

    lastMeshData = mesh;

    // Update stats
    const stats = mesh.stats || {}
    document.getElementById('meshNodeCount').textContent = (mesh.nodes || []).length
    document.getElementById('meshMsgCount').textContent = stats.messages_routed || 0
    document.getElementById('meshSatCount').textContent = stats.queen_to_satellite || 0
    document.getElementById('meshAggCount').textContent = stats.alerts_aggregated || 0

    // Populate dropdown (once)
    if (!dropdownPopulated && mesh.nodes.length > 0) {
      populateNodeDropdown(mesh)
      dropdownPopulated = true
    }

    // Draw map markers for all nodes
    drawMeshOnMap(mesh)

    // Draw mesh topology on canvas
    drawMeshCanvas(mesh)

    // Update relay log
    updateRelayLog(mesh.recent_relays || [])
  } catch (e) {
    console.warn("Mesh load failed", e)
  }
}

function populateNodeDropdown(mesh) {
  const sel = document.getElementById('nodeSelector')
  if (!sel) return;

  // Keep the "All Regions" option
  sel.innerHTML = '<option value="ALL">\u{1F30F} All Regions</option>'

  // Group by Queens
  const queens = mesh.nodes.filter(n => n.is_queen)
  const drones = mesh.nodes.filter(n => !n.is_queen)

  queens.forEach(q => {
    const label = q.label || q.id
    const lat = q.lat.toFixed(3)
    const lon = q.lon.toFixed(3)
    sel.innerHTML += `<option value="${q.id}">\u{1F451} ${q.id} \u2014 ${label} (${lat}, ${lon})</option>`

    // Add drones for this queen
    const myDrones = drones.filter(d => d.queen_id === q.id)
    myDrones.forEach(d => {
      const dlabel = d.label || d.id
      sel.innerHTML += `<option value="${d.id}">&nbsp;&nbsp;\u{1F41D} ${d.id} \u2014 ${dlabel}</option>`
    })
  })
}

function drawMeshOnMap(mesh) {
  if (!map) return;

  // Clear old markers/lines
  meshMarkers.forEach(m => map.removeLayer(m))
  meshLines.forEach(l => map.removeLayer(l))
  meshMarkers = []
  meshLines = []

  const nodes = mesh.nodes || []
  const links = mesh.links || []

  // Draw Queen markers (gold, larger)
  nodes.filter(n => n.is_queen).forEach(q => {
    const marker = L.circleMarker([q.lat, q.lon], {
      radius: 10,
      color: '#ffd700',
      fillColor: '#ffd700',
      fillOpacity: 0.9,
      weight: 3
    }).addTo(map)
    marker.bindTooltip(`\u{1F451} ${q.id}<br>${q.label || ''}<br>Alerts: ${q.alerts_sent}`, {
      permanent: false, direction: 'top'
    })
    meshMarkers.push(marker)
  })

  // Draw Drone markers (blue, smaller)
  nodes.filter(n => !n.is_queen).forEach(d => {
    const riskColor = d.risk_score > 0.7 ? '#ff4444' : d.risk_score > 0.4 ? '#ff8800' : '#0088cc'
    const marker = L.circleMarker([d.lat, d.lon], {
      radius: 6,
      color: riskColor,
      fillColor: riskColor,
      fillOpacity: 0.8,
      weight: 2
    }).addTo(map)
    marker.bindTooltip(`\u{1F41D} ${d.id}<br>${d.label || ''}<br>Risk: ${(d.risk_score || 0).toFixed(2)}`, {
      permanent: false, direction: 'top'
    })
    meshMarkers.push(marker)
  })

  // Draw LoRa links as dashed lines on map
  links.filter(l => l.type === 'lora').forEach(l => {
    const src = nodes.find(n => n.id === l.source)
    const tgt = nodes.find(n => n.id === l.target)
    if (!src || !tgt) return;

    const line = L.polyline([[src.lat, src.lon], [tgt.lat, tgt.lon]], {
      color: l.active ? 'rgba(0,180,255,0.5)' : 'rgba(150,150,150,0.3)',
      weight: 1,
      dashArray: '5 5'
    }).addTo(map)
    meshLines.push(line)
  })
}

function drawMeshCanvas(mesh) {
  const canvas = document.getElementById('meshCanvas')
  if (!canvas) return;
  const ctx = canvas.getContext('2d')
  const w = canvas.width
  const h = canvas.height

  // Clear
  ctx.fillStyle = '#001122'
  ctx.fillRect(0, 0, w, h)

  // Subtle grid
  ctx.strokeStyle = 'rgba(0,80,160,0.12)'
  ctx.lineWidth = 1
  for (let i = 0; i < w; i += 25) {
    ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, h); ctx.stroke()
  }
  for (let i = 0; i < h; i += 25) {
    ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(w, i); ctx.stroke()
  }

  const nodes = mesh.nodes || []
  const links = mesh.links || []
  if (nodes.length === 0) return;

  const queens = nodes.filter(n => n.is_queen)
  const drones = nodes.filter(n => !n.is_queen)

  // Layout: distribute Queens horizontally, Drones around each Queen
  const positions = {}
  const qSpacing = w / (queens.length + 1)
  const qY = h / 2

  queens.forEach((q, idx) => {
    const qx = qSpacing * (idx + 1)
    positions[q.id] = { x: qx, y: qY }

    // Position drones for this queen
    const myDrones = drones.filter(d => d.queen_id === q.id)
    const droneRadius = Math.min(qSpacing * 0.35, h * 0.3)
    myDrones.forEach((d, di) => {
      const angle = (Math.PI * 2 * di / myDrones.length) - Math.PI / 2
      positions[d.id] = {
        x: qx + Math.cos(angle) * droneRadius,
        y: qY + Math.sin(angle) * droneRadius
      }
    })
  })

  // Satellite
  const satX = w - 20
  const satY = 18
  meshAnimFrame++

  // Draw LoRa links
  links.filter(l => l.type === 'lora').forEach(l => {
    const src = positions[l.source]
    const tgt = positions[l.target]
    if (!src || !tgt) return;

    ctx.strokeStyle = l.active ? 'rgba(0,180,255,0.35)' : 'rgba(100,100,100,0.2)'
    ctx.lineWidth = l.active ? 1.5 : 1
    ctx.setLineDash([4, 4])
    ctx.beginPath()
    ctx.moveTo(src.x, src.y)
    ctx.lineTo(tgt.x, tgt.y)
    ctx.stroke()
    ctx.setLineDash([])

    if (l.active) {
      const t = ((meshAnimFrame * 0.025 + l.source.charCodeAt(l.source.length - 1) * 0.1) % 1)
      const dotX = src.x + (tgt.x - src.x) * t
      const dotY = src.y + (tgt.y - src.y) * t
      ctx.fillStyle = '#00ccff'
      ctx.beginPath()
      ctx.arc(dotX, dotY, 2, 0, Math.PI * 2)
      ctx.fill()
    }
  })

  // Satellite uplinks from each Queen
  queens.forEach(q => {
    const qp = positions[q.id]
    if (!qp) return;
    ctx.strokeStyle = 'rgba(255,215,0,0.3)'
    ctx.lineWidth = 1
    ctx.setLineDash([2, 5])
    ctx.beginPath()
    ctx.moveTo(qp.x, qp.y)
    ctx.lineTo(satX, satY)
    ctx.stroke()
    ctx.setLineDash([])
  })

  // Sat icon
  const satPulse = Math.sin(meshAnimFrame * 0.1) * 0.3 + 0.7
  ctx.globalAlpha = satPulse
  ctx.font = '14px sans-serif'
  ctx.fillText('\u{1F6F0}\uFE0F', satX - 8, satY + 5)
  ctx.globalAlpha = 1

  // Draw Drones
  drones.forEach(d => {
    const pos = positions[d.id]
    if (!pos) return;

    const pulse = Math.sin(meshAnimFrame * 0.07 + d.id.charCodeAt(d.id.length - 1)) * 2 + 9
    ctx.strokeStyle = 'rgba(0,180,255,0.15)'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.arc(pos.x, pos.y, pulse, 0, Math.PI * 2)
    ctx.stroke()

    const riskColor = d.risk_score > 0.7 ? '#ff4444' : d.risk_score > 0.4 ? '#ff8800' : '#0088cc'
    ctx.fillStyle = riskColor
    ctx.beginPath()
    ctx.arc(pos.x, pos.y, 5, 0, Math.PI * 2)
    ctx.fill()
    ctx.strokeStyle = '#00ccff'
    ctx.lineWidth = 1.5
    ctx.stroke()

    // Short label
    ctx.fillStyle = '#5599bb'
    ctx.font = '7px Inter, sans-serif'
    ctx.textAlign = 'center'
    const shortId = d.id.replace('D_', '').replace('_', '')
    ctx.fillText(shortId, pos.x, pos.y + 14)
    ctx.textAlign = 'left'
  })

  // Draw Queens
  queens.forEach((q, idx) => {
    const qp = positions[q.id]
    if (!qp) return;

    // Glow
    const glow = ctx.createRadialGradient(qp.x, qp.y, 3, qp.x, qp.y, 18)
    glow.addColorStop(0, 'rgba(255,215,0,0.35)')
    glow.addColorStop(1, 'rgba(255,215,0,0)')
    ctx.fillStyle = glow
    ctx.beginPath()
    ctx.arc(qp.x, qp.y, 18, 0, Math.PI * 2)
    ctx.fill()

    // Hexagon
    ctx.fillStyle = '#ffd700'
    ctx.beginPath()
    for (let i = 0; i < 6; i++) {
      const a = (Math.PI * 2 * i / 6) - Math.PI / 6
      const px = qp.x + Math.cos(a) * 9
      const py = qp.y + Math.sin(a) * 9
      if (i === 0) ctx.moveTo(px, py)
      else ctx.lineTo(px, py)
    }
    ctx.closePath()
    ctx.fill()

    // "Q" label
    ctx.fillStyle = '#001122'
    ctx.font = 'bold 8px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('Q', qp.x, qp.y + 3)

    // Region label
    ctx.fillStyle = '#ffd700'
    ctx.font = 'bold 7px Inter, sans-serif'
    const shortName = (q.label || q.id).split(',')[0].replace('National Park', 'NP')
    ctx.fillText(shortName, qp.x, qp.y + 22)
    ctx.textAlign = 'left'
  })

  // Title
  ctx.fillStyle = 'rgba(0,180,255,0.4)'
  ctx.font = '7px Inter, sans-serif'
  ctx.fillText(`MESH: ${queens.length}Q + ${drones.length}D`, 6, 12)
}

function updateRelayLog(relays) {
  const container = document.getElementById('meshRelayLog')
  if (!container || relays.length === 0) return;

  const last5 = relays.slice(-5).reverse()
  container.innerHTML = last5.map(r => {
    const path = (r.path || []).join(' \u2192 ')
    const isSat = r.type === 'satellite_uplink'
    const cls = isSat ? 'relay-entry satellite' : 'relay-entry'
    const icon = isSat ? '\u{1F6F0}\uFE0F' : '\u{1F4E1}'
    return `<div class="${cls}">${icon} ${path}</div>`
  }).join('')
}

// Zoom map to selected node/region
function onNodeSelected(nodeId) {
  if (!lastMeshData || !map) return;
  const nodes = lastMeshData.nodes || []

  if (nodeId === 'ALL') {
    // Fit all nodes
    if (nodes.length > 0) {
      const bounds = L.latLngBounds(nodes.map(n => [n.lat, n.lon]))
      map.fitBounds(bounds, { padding: [30, 30] })
    }
    return
  }

  const node = nodes.find(n => n.id === nodeId)
  if (!node) return;

  if (node.is_queen) {
    // Zoom to Queen + its drones
    const myDrones = nodes.filter(n => n.queen_id === nodeId)
    const group = [node, ...myDrones]
    const bounds = L.latLngBounds(group.map(n => [n.lat, n.lon]))
    map.fitBounds(bounds, { padding: [40, 40] })
  } else {
    map.setView([node.lat, node.lon], 15)
  }
}

async function refreshAll() {
  await loadHistory()
  await loadStatus()
  await loadDetections()
  await loadMesh()
  if (!map) initMap();
}

window.addEventListener('load', () => {
  initMap();
  refreshAll()

  // Node selector → zoom map
  const sel = document.getElementById('nodeSelector')
  if (sel) {
    sel.addEventListener('change', (e) => onNodeSelected(e.target.value))
  }

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

  // Animate mesh canvas at 20fps
  setInterval(() => {
    if (lastMeshData) drawMeshCanvas(lastMeshData)
  }, 50)
})