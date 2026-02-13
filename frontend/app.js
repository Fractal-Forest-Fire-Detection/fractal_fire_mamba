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
    API_ROOT = new URL('/api', origin).toString()
  }
} catch (e) {
  API_ROOT = 'http://127.0.0.1:8000/api'
}

async function fetchJson(path) {
  const res = await fetch(path)
  return res.json()
}

// Initialize chart
// Initialize chart
const ctx = document.getElementById('fusedChart').getContext('2d')
const fusedChart = new Chart(ctx, {
  type: 'line',
  data: { labels: [], datasets: [{ label: 'Fused Score', data: [], borderColor: '#ff6b35', backgroundColor: 'rgba(255,107,53,0.12)', tension: 0.2 }] },
  options: { scales: { y: { min: 0, max: 1 } }, plugins: { legend: { display: false } } }
})

const ctxTemp = document.getElementById('tempChart').getContext('2d')
const tempChart = new Chart(ctxTemp, {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      { label: 'Temp (°C)', data: [], borderColor: '#ff3535', tension: 0.2, yAxisID: 'y' },
      { label: 'Env Risk', data: [], borderColor: '#ffa500', tension: 0.2, yAxisID: 'y1' }
    ]
  },
  options: {
    interaction: { mode: 'index', intersect: false },
    scales: {
      y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Temp' } },
      y1: { type: 'linear', display: true, position: 'right', min: 0, max: 1, grid: { drawOnChartArea: false }, title: { display: true, text: 'Risk' } }
    }
  }
})

const ctxChem = document.getElementById('chemVisChart').getContext('2d')
const chemVisChart = new Chart(ctxChem, {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      { label: 'Chemical (VOC)', data: [], borderColor: '#35b8ff', tension: 0.2 },
      { label: 'Visual (Smoke)', data: [], borderColor: '#9b35ff', tension: 0.2 }
    ]
  },
  options: { scales: { y: { min: 0, max: 1 } } }
})

const ctxHurst = document.getElementById('hurstChart').getContext('2d')
const hurstChart = new Chart(ctxHurst, {
  type: 'line',
  data: {
    labels: [],
    datasets: [{ label: 'Hurst (H)', data: [], borderColor: '#00e0df', backgroundColor: 'rgba(0,224,223,0.1)', tension: 0.1 }]
  },
  options: {
    scales: { y: { min: 0, max: 1 } },
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
  options: { scales: { y: { recommendedMin: -1, recommendedMax: 1 } } }
})

function updateNodeInfo(data) {
  document.getElementById('nodeId').textContent = data.node_id
  document.getElementById('riskTier').textContent = data.risk_tier
  document.getElementById('fusedScore').textContent = data.mamba_ssm.fused_score
  document.getElementById('mambaScoreVal').textContent = data.mamba_ssm.fused_score
  // Map 'visual_score' from backend to Visual Confidence display
  document.getElementById('visualConfVal').textContent = (data.vision.visual_score || 0).toFixed(2)

  document.getElementById('temporalConf').textContent = data.mamba_ssm.temporal_confidence
  document.getElementById('visionMode').textContent = data.vision.vision_mode
  document.getElementById('visionMode').textContent = data.vision.vision_mode
  document.getElementById('cameraHealth').textContent = data.vision.camera_health.health_score

  // NEW: System Status & Weights
  if (data.system_status) {
    document.getElementById('activePhase').textContent = data.system_status.phase
    document.getElementById('finalRiskDisplay').textContent = data.system_status.final_risk.toFixed(2)

    const w = data.system_status.weights
    document.getElementById('wVisVal').textContent = w.visual + '%'
    document.getElementById('wVisBar').style.width = w.visual + '%'

    document.getElementById('wThermVal').textContent = w.thermal + '%'
    document.getElementById('wThermBar').style.width = w.thermal + '%'

    document.getElementById('wChemVal').textContent = w.chemical + '%'
    document.getElementById('wChemBar').style.width = w.chemical + '%'

    // Color code risk
    const riskEl = document.getElementById('finalRiskDisplay')
    if (data.system_status.final_risk > 0.8) riskEl.style.color = '#ff4d4f'
    else if (data.system_status.final_risk > 0.5) riskEl.style.color = '#ff6b35'
    else riskEl.style.color = '#fff'
  }

  // Update map if location is present
  if (data.location && data.location.latitude) {
    updateNodeMarker(data.location, data.risk_tier)
  }

  // Fractal Gate (Phase-2)
  const h = data.fractal.hurst || 0.5
  document.getElementById('hurstVal').textContent = h.toFixed(2)
  document.getElementById('hurstBar').style.width = Math.min(100, (h / 2.0) * 100) + '%'
  document.getElementById('fractalStatus').textContent = data.fractal.status || 'WAITING'
  document.getElementById('fractalStatus').style.color = data.fractal.has_structure ? '#ff4d4f' : '#33b864'

  // Chaos Kernel (Phase-3)
  const ly = data.chaos.lyapunov || 0.0
  document.getElementById('lyapVal').textContent = ly.toFixed(2)
  // Visualize lyapunov: range typically -1 to 1. Map -1..1 to 0..100%
  // 0 is middle.
  const lyPct = Math.min(100, Math.max(0, (ly + 1) * 50))
  document.getElementById('lyapBar').style.width = lyPct + '%'
  document.getElementById('chaosStatus').textContent = data.chaos.status || 'WAITING'
  document.getElementById('chaosStatus').style.color = data.chaos.is_unstable ? '#ff4d4f' : '#33b864'

  // Component Breakdown
  const c = data.components || {}
  document.getElementById('scoreChem').textContent = (c.chemical || 0).toFixed(2)
  document.getElementById('barChem').style.width = ((c.chemical || 0) * 100) + '%'

  document.getElementById('scoreVis').textContent = (c.visual || 0).toFixed(2)
  document.getElementById('barVis').style.width = ((c.visual || 0) * 100) + '%'

  document.getElementById('scoreEnv').textContent = (c.environmental || 0).toFixed(2)
  document.getElementById('barEnv').style.width = ((c.environmental || 0) * 100) + '%'
}



async function loadHistory() {
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
  window._lastSeries = h.series
}

async function loadStatus() {
  const s = await fetchJson(API_ROOT + '/status')
  updateNodeInfo(s)
  // fetch persisted alerts and show per-node first
  const allAlertsResp = await fetchJson(API_ROOT + '/alerts')
  const allAlerts = allAlertsResp.alerts || []
  // update map markers for alerts that include location
  clearAlertMarkers()
  allAlerts.forEach(a => addOrUpdateAlertMarker(a))
  // per-node alerts
  const nodeAlerts = allAlerts.filter(a => a.node_id === s.node_id)
  if (nodeAlerts.length) {
    renderAlerts(nodeAlerts)
    // zoom to most severe (RED > ORANGE > YELLOW) if available
    const red = nodeAlerts.find(x => x.level === 'RED')
    const orange = nodeAlerts.find(x => x.level === 'ORANGE')
    const yellow = nodeAlerts.find(x => x.level === 'YELLOW')
    const target = red || orange || yellow
    if (target) zoomToAlert(target, { zoom: 15 })
  }
}

// Map Logic
let map = null;
let nodeMarker = null;
let detectionMarkers = {};

function initMap() {
  // Default to Australia if no location yet
  map = L.map('map').setView([-35.714, 150.179], 13);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);
}

function updateNodeMarker(loc, tier) {
  if (!map) initMap(); // Lazy init

  const lat = loc.latitude;
  const lng = loc.longitude;
  const color = tier === 'CRITICAL' ? '#ff4d4f' : tier === 'ELEVATED' ? '#ff6b35' : '#33b864';

  if (nodeMarker) {
    nodeMarker.setLatLng([lat, lng]);
    nodeMarker.setStyle({ color: color, fillColor: color });
    // Don't auto-center every update to allow user panning, unless it's way off?
    // map.setView([lat, lng]); 
  } else {
    nodeMarker = L.circleMarker([lat, lng], {
      radius: 8,
      color: color,
      fillColor: color,
      fillOpacity: 1.0
    }).addTo(map);
    map.setView([lat, lng], 13);
  }
}

function zoomToAlert(alert, opts = { zoom: 16 }) {
  if (!map) return;
  // Alerts from backend might not have location, depends on source
  // But we check before calling
  // Actually, local alerts array doesn't have location attached easily unless we link it
  // But 'focusLatestRed' fetches correct alerts with location.

  // If alert object has Lat/Lng (e.g. from backend)
  if (alert.location) {
    map.setView([alert.location.latitude, alert.location.longitude], opts.zoom);
    L.popup()
      .setLatLng([alert.location.latitude, alert.location.longitude])
      .setContent(`<strong>${alert.level} ALERT</strong><br>${new Date(alert.timestamp).toLocaleTimeString()}`)
      .openOn(map);
  }
}


// Focus the latest global RED alert
// Focus the latest global RED alert
async function focusLatestRed() {
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
}

async function ackAlert(id) {
  try {
    await fetch(API_ROOT + `/alerts/${id}/ack`, { method: 'POST' })
    // refresh alerts
    await loadStatus()
  } catch (e) {
    console.error('ack failed', e)
  }
}

// Map and death vectors (Restored)

// Detections layer (UAV detections)
async function loadDetections() {
  try {
    const r = await fetchJson(API_ROOT + '/detections')
    const dets = r.detections || []

    // Update Camera Feed if detection exists
    const feedImg = document.getElementById('cameraFeed')
    const feedPlaceholder = document.getElementById('cameraPlaceholder')
    const camStatus = document.getElementById('camStatus')

    if (dets.length > 0) {
      const latest = dets[0] // Assuming latest is first or only
      let src = ''
      if (latest.image_url) src = latest.image_url
      else if (latest.image_b64) src = `data:image/jpeg;base64,${latest.image_b64}`

      if (src) {
        feedImg.src = src
        feedImg.style.display = 'block'
        feedPlaceholder.style.display = 'none'
        camStatus.textContent = 'DETECTING'
        camStatus.style.color = '#ff4d4f'
      }
    } else {
      // Keep last image or showing placeholder? 
      // For now, let's revert to placeholder if no active detection to simulate "live" feed behavior clearing up
      // Or we could leave it. Let's leave it if it was set, but maybe show "Scanning..."
      // Actually, let's just keep the last image if available, or reset if we want strict "current state".
      // Given the demo nature, it might flicker if we reset. Let's only update if we have something.
      if (feedImg.style.display === 'none') {
        camStatus.textContent = 'SCANNING'
        camStatus.style.color = '#33b864'
      }
    }

    // Map markers
    dets.forEach(d => {
      if (!d.location) return
      const id = d.id
      const lat = d.location.latitude
      const lng = d.location.longitude
      const conf = d.confidence || 0
      const color = conf >= 0.8 ? '#ff4d4f' : conf >= 0.6 ? '#ff6b35' : '#f7d154'

      if (!map) initMap();

      if (!detectionMarkers[id]) {
        const icon = L.circleMarker([lat, lng], { radius: 6, color: color, fillColor: color, fillOpacity: 0.9 }).addTo(map)
        let popupHtml = `<strong>UAV detection</strong><br/>confidence: ${conf.toFixed(2)}<br/>${new Date(d.timestamp).toLocaleString()}`
        if (d.image_url) { popupHtml += `<br/><img src="${d.image_url}" style="max-width:180px;max-height:120px;display:block;margin-top:6px"/>` }
        else if (d.image_b64) { popupHtml += `<br/><img src="data:image/jpeg;base64,${d.image_b64}" style="max-width:180px;max-height:120px;display:block;margin-top:6px"/>` }
        icon.bindPopup(popupHtml)
        detectionMarkers[id] = icon
      }
    })

  } catch (e) {
    console.error('failed to load detections', e)
  }
}

function findAlertsFromSeries(series) {
  // Simple rule-based alerts (explainable):
  // ORANGE: fused_score >= 0.6, RED: fused_score >= 0.8
  const alerts = []
  series.forEach(pt => {
    const score = pt.fused_score
    if (score >= 0.8) alerts.push({ level: 'RED', score, ts: pt.timestamp })
    else if (score >= 0.6) alerts.push({ level: 'ORANGE', score, ts: pt.timestamp })
    else if (score >= 0.5) alerts.push({ level: 'YELLOW', score, ts: pt.timestamp })
  })
  return alerts.slice(-10).reverse()
}

function renderAlerts(alerts) {
  const container = document.getElementById('alertsList')
  container.innerHTML = ''
  if (!alerts || alerts.length === 0) {
    container.innerHTML = '<p style="color:var(--muted)">No alerts in recent history</p>'
    return
  }
  const ul = document.createElement('ul')
  alerts.forEach(a => {
    const li = document.createElement('li')
    // If alert came from backend, may have timestamp and acknowledged flag
    const time = a.timestamp ? new Date(a.timestamp).toLocaleString() : (a.ts ? new Date(a.ts).toLocaleString() : '')
    const ackButton = a.id ? `<button data-id="${a.id}" class="ack">Ack</button>` : ''
    li.innerHTML = `<strong style="color:${a.level === 'RED' ? '#ff4d4f' : a.level === 'ORANGE' ? '#ff6b35' : '#f7d154'}">${a.level}</strong> — ${time} — score: ${a.score} ${ackButton} <button class="zoom" data-ts="${a.timestamp}">Zoom</button>`
    ul.appendChild(li)
  })
  container.appendChild(ul)
  // attach ack handlers
  Array.from(container.querySelectorAll('button.ack')).forEach(b => {
    b.addEventListener('click', ev => {
      const id = Number(ev.target.dataset.id)
      ackAlert(id)
    })
  })
  // attach zoom handlers
  Array.from(container.querySelectorAll('button.zoom')).forEach(b => {
    b.addEventListener('click', ev => {
      const ts = ev.target.dataset.ts
      const a = alerts.find(x => x.timestamp === ts)
      // Local heuristic alerts don't have location attached in 'alerts' array easily
      // So zoom might fail unless we attach location to them. 
      // For now, let's just log or ignore if no loc.
      // Actually, standard alerts comes from backend with loc. 
      // The local heuristics (loadHistory) don't have loc.
      if (a && a.location) zoomToAlert(a, { zoom: 16 })
    })
  })
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

async function refreshAll() {
  await loadHistory()
  await loadStatus()
  await loadDetections()
}

window.addEventListener('load', () => {
  refreshAll()
  // Wire CSV download
  document.getElementById('downloadCsv').addEventListener('click', async () => {
    const h = await fetchJson(API_ROOT + '/history')
    downloadCSV(h.series)
  })
  // Refresh every 10s
  setInterval(refreshAll, 10000)
})
