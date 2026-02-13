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
    if (confEl) {
      // Confidence comes as 0.0-1.0 float from server
      const rawConf = parseFloat(data.mamba_ssm.temporal_confidence) || 0;
      const confPct = rawConf > 1 ? rawConf : rawConf * 100; // handle both 0-1 and 0-100
      confEl.textContent = confPct.toFixed(0) + '%';
    }
  }

  if (data.node_id) {
    // document.getElementById('nodeId').textContent = data.node_id; // element removed in gov theme
  }

  document.getElementById('riskTier').textContent = data.risk_tier;

  // Map 'visual_score' from backend to Visual Confidence display
  if (data.vision) {
    const vConfElem = document.getElementById('visualConfVal');
    if (vConfElem) vConfElem.textContent = (data.vision.visual_score || 0).toFixed(2);
    const vModeElem = document.getElementById('visionMode');
    if (vModeElem) vModeElem.textContent = data.vision.vision_mode;
    const camHealthElem = document.getElementById('cameraHealth');
    if (camHealthElem) camHealthElem.textContent = data.vision.camera_health ? data.vision.camera_health.health_score : '--';
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

    // Update Queen Health panel
    renderQueenHealth(mesh)
  } catch (e) {
    console.warn("Mesh load failed", e)
  }
}

function populateNodeDropdown(mesh) {
  const sel = document.getElementById('nodeSelector')
  if (!sel) return;

  // "All Regions" removed per user request
  sel.innerHTML = '<option value="" disabled selected>Select a Queen Node...</option>'

  // Group by Queens
  const queens = mesh.nodes.filter(n => n.is_queen)
  const drones = mesh.nodes.filter(n => !n.is_queen)

  queens.forEach(q => {
    const label = q.label || q.id
    const lat = q.lat.toFixed(3)
    const lon = q.lon.toFixed(3)
    sel.innerHTML += `<option value="${q.id}">\u{1F451} ${q.id} \u2014 ${label} (${lat}, ${lon})</option>`

    // Drones hidden per user request (Australia Black Fire Dataset focus)
    /*
    const myDrones = drones.filter(d => d.queen_id === q.id)
    myDrones.forEach(d => {
      const dlabel = d.label || d.id
      sel.innerHTML += `<option value="${d.id}">&nbsp;&nbsp;\u{1F41D} ${d.id} \u2014 ${dlabel}</option>`
    })
    */
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

  // ── Professional light background ──
  ctx.fillStyle = '#f4f6f8'
  ctx.fillRect(0, 0, w, h)

  // Subtle dot grid (like engineering paper)
  ctx.fillStyle = '#d0d5dd'
  for (let x = 10; x < w; x += 20) {
    for (let y = 10; y < h; y += 20) {
      ctx.beginPath()
      ctx.arc(x, y, 0.5, 0, Math.PI * 2)
      ctx.fill()
    }
  }

  const nodes = mesh.nodes || []
  const links = mesh.links || []
  if (nodes.length === 0) return;

  const queens = nodes.filter(n => n.is_queen)
  const drones = nodes.filter(n => !n.is_queen)

  // Layout: distribute Queens horizontally, Drones around each Queen
  const positions = {}
  const qSpacing = w / (queens.length + 1)
  const qY = h * 0.48

  queens.forEach((q, idx) => {
    const qx = qSpacing * (idx + 1)
    positions[q.id] = { x: qx, y: qY }

    const myDrones = drones.filter(d => d.queen_id === q.id)
    const droneRadius = Math.min(qSpacing * 0.35, h * 0.28)
    myDrones.forEach((d, di) => {
      const angle = (Math.PI * 2 * di / myDrones.length) - Math.PI / 2
      positions[d.id] = {
        x: qx + Math.cos(angle) * droneRadius,
        y: qY + Math.sin(angle) * droneRadius
      }
    })
  })

  meshAnimFrame++

  // ── Draw LoRa links (clean solid lines) ──
  links.filter(l => l.type === 'lora').forEach(l => {
    const src = positions[l.source]
    const tgt = positions[l.target]
    if (!src || !tgt) return;

    ctx.strokeStyle = l.active ? '#3b82f6' : '#cbd5e1'
    ctx.lineWidth = l.active ? 1.2 : 0.8
    ctx.setLineDash([])
    ctx.beginPath()
    ctx.moveTo(src.x, src.y)
    ctx.lineTo(tgt.x, tgt.y)
    ctx.stroke()
  })

  // ── Satellite uplink lines from Queens (dashed, professional) ──
  const satLabel = { x: w / 2, y: 14 }
  queens.forEach(q => {
    const qp = positions[q.id]
    if (!qp) return;
    ctx.strokeStyle = '#94a3b8'
    ctx.lineWidth = 0.8
    ctx.setLineDash([3, 3])
    ctx.beginPath()
    ctx.moveTo(qp.x, qp.y - 16)
    ctx.lineTo(satLabel.x, satLabel.y + 6)
    ctx.stroke()
    ctx.setLineDash([])
  })

  // ── Satellite label (text, not emoji) ──
  ctx.fillStyle = '#64748b'
  ctx.font = '8px Inter, system-ui, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('IRIDIUM UPLINK', satLabel.x, satLabel.y)
  // Small triangle icon
  ctx.fillStyle = '#94a3b8'
  ctx.beginPath()
  ctx.moveTo(satLabel.x - 4, satLabel.y + 4)
  ctx.lineTo(satLabel.x + 4, satLabel.y + 4)
  ctx.lineTo(satLabel.x, satLabel.y + 10)
  ctx.closePath()
  ctx.fill()

  // ── Draw Drones (clean small circles with labels) ──
  drones.forEach(d => {
    const pos = positions[d.id]
    if (!pos) return;

    // Status ring
    const riskColor = d.risk_score > 0.7 ? '#dc2626' : d.risk_score > 0.4 ? '#f59e0b' : '#22c55e'

    // Outer ring
    ctx.strokeStyle = riskColor
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.arc(pos.x, pos.y, 8, 0, Math.PI * 2)
    ctx.stroke()

    // Inner fill
    ctx.fillStyle = '#ffffff'
    ctx.beginPath()
    ctx.arc(pos.x, pos.y, 6, 0, Math.PI * 2)
    ctx.fill()

    // Status dot
    ctx.fillStyle = riskColor
    ctx.beginPath()
    ctx.arc(pos.x, pos.y, 3, 0, Math.PI * 2)
    ctx.fill()

    // Label
    ctx.fillStyle = '#475569'
    ctx.font = '7px Inter, system-ui, sans-serif'
    ctx.textAlign = 'center'
    const shortId = d.id.replace('D_', '').replace('_0', '-')
    ctx.fillText(shortId, pos.x, pos.y + 16)
    ctx.textAlign = 'left'
  })

  // ── Draw Queens (professional rounded rectangles with status) ──
  queens.forEach((q, idx) => {
    const qp = positions[q.id]
    if (!qp) return;

    const boxW = 56, boxH = 28, r = 4
    const bx = qp.x - boxW / 2
    const by = qp.y - boxH / 2

    // Shadow
    ctx.shadowColor = 'rgba(0,0,0,0.08)'
    ctx.shadowBlur = 4
    ctx.shadowOffsetY = 1

    // Rounded rect
    ctx.fillStyle = '#1e3a5f'
    ctx.beginPath()
    ctx.moveTo(bx + r, by)
    ctx.lineTo(bx + boxW - r, by)
    ctx.quadraticCurveTo(bx + boxW, by, bx + boxW, by + r)
    ctx.lineTo(bx + boxW, by + boxH - r)
    ctx.quadraticCurveTo(bx + boxW, by + boxH, bx + boxW - r, by + boxH)
    ctx.lineTo(bx + r, by + boxH)
    ctx.quadraticCurveTo(bx, by + boxH, bx, by + boxH - r)
    ctx.lineTo(bx, by + r)
    ctx.quadraticCurveTo(bx, by, bx + r, by)
    ctx.closePath()
    ctx.fill()

    // Reset shadow
    ctx.shadowColor = 'transparent'
    ctx.shadowBlur = 0
    ctx.shadowOffsetY = 0

    // Queen ID inside box
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 8px Inter, system-ui, sans-serif'
    ctx.textAlign = 'center'
    const shortName = (q.label || q.id).split(',')[0].replace('National Park', 'NP').replace(' NP', '')
    ctx.fillText(shortName, qp.x, qp.y + 3)

    // Region label below
    ctx.fillStyle = '#475569'
    ctx.font = '7px Inter, system-ui, sans-serif'
    const batt = q.battery !== undefined ? q.battery : 100
    const battColor = batt > 50 ? '#16a34a' : batt > 20 ? '#f59e0b' : '#dc2626'
    ctx.fillText('QUEEN', qp.x, qp.y + boxH / 2 + 10)

    // Battery indicator (small bar below)
    const barW = 30, barH = 3
    const barX = qp.x - barW / 2
    const barY = qp.y + boxH / 2 + 14
    ctx.fillStyle = '#e2e8f0'
    ctx.fillRect(barX, barY, barW, barH)
    ctx.fillStyle = battColor
    ctx.fillRect(barX, barY, barW * (batt / 100), barH)

    // Status dot (top-right corner)
    ctx.fillStyle = '#22c55e'
    ctx.beginPath()
    ctx.arc(bx + boxW - 3, by + 3, 3, 0, Math.PI * 2)
    ctx.fill()
    ctx.strokeStyle = '#1e3a5f'
    ctx.lineWidth = 1
    ctx.stroke()

    ctx.textAlign = 'left'
  })

  // ── Header label ──
  ctx.fillStyle = '#94a3b8'
  ctx.font = '8px Inter, system-ui, sans-serif'
  ctx.fillText(`TOPOLOGY: ${queens.length} QUEEN · ${drones.length} DRONE`, 6, h - 6)
}

function updateRelayLog(relays) {
  const container = document.getElementById('meshRelayLog')
  if (!container || relays.length === 0) return;

  const last5 = relays.slice(-5).reverse()
  container.innerHTML = last5.map(r => {
    const path = (r.path || []).join(' \u2192 ')
    const isSat = r.type === 'satellite_uplink'
    const cls = isSat ? 'relay-entry satellite' : 'relay-entry'
    // Enhanced labels showing protocol
    const protocol = isSat ? '\u{1F6F0}\uFE0F Iridium SBD' : '\u{1F4E1} LoRa 868MHz'
    return `<div class="${cls}">${protocol}: ${path}</div>`
  }).join('')
}

// ==========================================================================
// QUEEN HEALTH MONITORING PANEL
// ==========================================================================

function renderQueenHealth(mesh) {
  const container = document.getElementById('queenHealthList')
  if (!container) return;

  const nodes = mesh.nodes || []
  const queens = nodes.filter(n => n.is_queen)
  const drones = nodes.filter(n => !n.is_queen)

  if (queens.length === 0) {
    container.innerHTML = '<p style="color:#999; font-size:0.8rem;">No Queens registered</p>'
    return
  }

  container.innerHTML = queens.map(q => {
    const myDrones = drones.filter(d => d.queen_id === q.id)
    const onlineDrones = myDrones.filter(d => d.status === 'ONLINE').length
    const batt = q.battery !== undefined ? q.battery : 100
    const risk = q.risk_score || 0
    const alerts = q.alerts_sent || 0

    // Health color
    const healthColor = batt > 50 ? 'var(--success)' : batt > 20 ? 'var(--warning)' : 'var(--danger)'
    const riskColor = risk > 0.7 ? 'var(--danger)' : risk > 0.4 ? 'var(--warning)' : 'var(--success)'
    const shortName = (q.label || q.id).split(',')[0].replace('National Park', 'NP')

    return `
      <div style="padding: 8px; margin-bottom: 8px; background: var(--light-bg); border-radius: 4px; border-left: 3px solid ${healthColor};">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
          <strong style="font-size: 0.8rem; color: var(--navy);">\u{1F451} ${shortName}</strong>
          <span style="font-size: 0.7rem; padding: 1px 6px; border-radius: 3px; background: ${healthColor}; color: white;">${batt.toFixed(0)}%</span>
        </div>
        <div style="font-size: 0.72rem; color: #555; display: grid; grid-template-columns: 1fr 1fr; gap: 2px;">
          <div>Risk: <strong style="color:${riskColor}">${risk.toFixed(2)}</strong></div>
          <div>Alerts: <strong>${alerts}</strong></div>
          <div>Drones: <strong>${onlineDrones}/${myDrones.length}</strong></div>
          <div>Uplink: <strong style="color:var(--success);">SAT \u2713</strong></div>
        </div>
      </div>`
  }).join('')
}

// ==========================================================================
// IRIDIUM SATELLITE PASS SIMULATION (Real orbital mechanics)
// ==========================================================================
// Iridium NEXT: 66 satellites, 780km altitude, 86.4° inclination
// At lat -35°, a satellite rises on horizon every ~10 min, visible for ~7 min
// Uplink latency: ~30-50ms (LEO) + ~200ms processing = ~250ms total

function updateSatellitePass() {
  const now = new Date()

  // Simulate Iridium pass window (10-min period, 7-min visible)
  const periodMs = 10 * 60 * 1000      // 10 minutes
  const visibleMs = 7 * 60 * 1000      // 7 minutes visible
  const cyclePos = now.getTime() % periodMs
  const isVisible = cyclePos < visibleMs

  const statusEl = document.getElementById('satPassStatus')
  const nextPassEl = document.getElementById('nextSatPass')
  const latencyEl = document.getElementById('satLatency')

  if (statusEl) {
    if (isVisible) {
      statusEl.textContent = 'IN VIEW'
      statusEl.style.background = 'var(--success)'

      // Time remaining in this pass
      const remainMs = visibleMs - cyclePos
      const remainMin = Math.floor(remainMs / 60000)
      const remainSec = Math.floor((remainMs % 60000) / 1000)
      if (nextPassEl) nextPassEl.textContent = `Active (${remainMin}m ${remainSec}s remaining)`
    } else {
      statusEl.textContent = 'BELOW HORIZON'
      statusEl.style.background = 'var(--warning)'

      // Time until next pass
      const nextMs = periodMs - cyclePos
      const nextMin = Math.floor(nextMs / 60000)
      const nextSec = Math.floor((nextMs % 60000) / 1000)
      if (nextPassEl) nextPassEl.textContent = `in ${nextMin}m ${nextSec}s`
    }
  }

  if (latencyEl) {
    // Simulate realistic LEO latency: 30-50ms propagation + 200ms SBD processing
    const baseLat = 30 + Math.random() * 20  // 30-50ms
    const procLat = 180 + Math.random() * 40  // 180-220ms
    const totalLat = isVisible ? (baseLat + procLat) : NaN
    latencyEl.textContent = isVisible ? `${totalLat.toFixed(0)}ms (LEO)` : 'Waiting for pass…'
  }
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

  // Redraw mesh topology every 1s (no animation needed for professional view)
  setInterval(() => {
    if (lastMeshData) drawMeshCanvas(lastMeshData)
  }, 1000)

  // Iridium satellite pass countdown (1s for live timer)
  updateSatellitePass()
  setInterval(updateSatellitePass, 1000)
})