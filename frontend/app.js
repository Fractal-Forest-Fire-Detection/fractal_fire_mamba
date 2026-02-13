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
const ctx = document.getElementById('fusedChart').getContext('2d')
const fusedChart = new Chart(ctx, {
  type: 'line',
  data: { labels: [], datasets: [{ label: 'Fused Score', data: [], borderColor: '#ff6b35', backgroundColor: 'rgba(255,107,53,0.12)', tension: 0.2 }] },
  options: { scales: { y: { min: 0, max: 1 } }, plugins: { legend: { display: false } } }
})

function updateNodeInfo(data) {
  document.getElementById('nodeId').textContent = data.node_id
  document.getElementById('riskTier').textContent = data.risk_tier
  document.getElementById('fusedScore').textContent = data.mamba_ssm.fused_score
  document.getElementById('mambaScoreVal').textContent = data.mamba_ssm.fused_score
  // Map 'visual_score' from backend to YOLO confidence display
  document.getElementById('yoloScoreVal').textContent = (data.vision.visual_score || 0).toFixed(2)

  document.getElementById('temporalConf').textContent = data.mamba_ssm.temporal_confidence
  document.getElementById('visionMode').textContent = data.vision.vision_mode
  document.getElementById('cameraHealth').textContent = data.vision.camera_health.health_score

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
  const values = h.series.map(p => p.fused_score)
  fusedChart.data.labels = labels
  fusedChart.data.datasets[0].data = values
  fusedChart.update()
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

// Map and death vectors
let map
function initMap() {
  map = L.map('map').setView([37.7749, -122.4194], 13)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap contributors' }).addTo(map)
}

// Manage alert markers on the map
const alertMarkers = {}

function clearAlertMarkers() {
  Object.values(alertMarkers).forEach(obj => {
    try { if (obj.marker) map.removeLayer(obj.marker) } catch (e) { }
    try { if (obj.ring) map.removeLayer(obj.ring) } catch (e) { }
  })
  for (const k in alertMarkers) delete alertMarkers[k]
}

function addOrUpdateAlertMarker(alert) {
  if (!alert || !alert.location) return null
  const id = alert.id || (`${alert.node_id}_${alert.timestamp}`)
  const lat = alert.location.latitude
  const lng = alert.location.longitude
  const color = alert.level === 'RED' ? '#ff4d4f' : alert.level === 'ORANGE' ? '#ff6b35' : '#f7d154'

  // compute ring radius by severity (meters)
  const severityRadius = alert.level === 'RED' ? 200 : alert.level === 'ORANGE' ? 120 : 60

  if (alertMarkers[id]) {
    const obj = alertMarkers[id]
    if (obj.marker) obj.marker.setLatLng([lat, lng])
    if (obj.ring) obj.ring.setLatLng([lat, lng])
    if (obj.marker) obj.marker.setPopupContent(`<strong>${alert.level}</strong> ${alert.message || ''}`)
    return obj.marker
  }

  const marker = L.circleMarker([lat, lng], { radius: 8, color: color, fillColor: color, fillOpacity: 0.9 }).addTo(map)
  marker.bindPopup(`<strong>${alert.level}</strong><br/>${alert.message || ''}<br/>${new Date(alert.timestamp).toLocaleString()}`)
  const ring = L.circle([lat, lng], { radius: severityRadius, color: color, weight: 2, fill: false, opacity: 0.35 }).addTo(map)
  alertMarkers[id] = { marker, ring }
  return marker
}

function zoomToAlert(alert, opts = { zoom: 15 }) {
  if (!alert || !alert.location) return
  const lat = alert.location.latitude
  const lng = alert.location.longitude
  map.setView([lat, lng], opts.zoom || 15)
  const m = addOrUpdateAlertMarker(alert)
  if (m) m.openPopup()
}

async function loadDeathVectors() {
  const v = await fetchJson(API_ROOT + '/death_vectors')
  v.vectors.forEach(vec => {
    const from = [vec.from.lat, vec.from.lng]
    const to = [vec.to.lat, vec.to.lng]
    L.polyline([from, to], { color: '#ff6b35', weight: 3, opacity: 0.9 }).addTo(map)
    L.circle(from, { radius: 40, color: '#ff6b35', fill: false }).addTo(map)
  })
}

// Detections layer (UAV detections)
const detectionMarkers = {}

function clearDetectionMarkers() {
  Object.values(detectionMarkers).forEach(m => {
    try { map.removeLayer(m) } catch (e) { }
  })
  for (const k in detectionMarkers) delete detectionMarkers[k]
}

async function loadDetections() {
  try {
    const r = await fetchJson(API_ROOT + '/detections')
    const dets = r.detections || []
    clearDetectionMarkers()
    dets.forEach(d => {
      if (!d.location) return
      const id = d.id
      const lat = d.location.latitude
      const lng = d.location.longitude
      const conf = d.confidence || 0
      const color = conf >= 0.8 ? '#ff4d4f' : conf >= 0.6 ? '#ff6b35' : '#f7d154'
      const icon = L.circleMarker([lat, lng], { radius: 6, color: color, fillColor: color, fillOpacity: 0.9 }).addTo(map)
      let popupHtml = `<strong>UAV detection</strong><br/>confidence: ${conf.toFixed(2)}<br/>${new Date(d.timestamp).toLocaleString()}`
      if (d.image_url) { popupHtml += `<br/><img src="${d.image_url}" style="max-width:180px;max-height:120px;display:block;margin-top:6px"/>` }
      else if (d.image_b64) { popupHtml += `<br/><img src="data:image/jpeg;base64,${d.image_b64}" style="max-width:180px;max-height:120px;display:block;margin-top:6px"/>` }
      icon.bindPopup(popupHtml)
      detectionMarkers[id] = icon
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
      if (a) zoomToAlert(a, { zoom: 16 })
    })
  })
}

function downloadCSV(series) {
  const rows = [['timestamp', 'fused_score']]
  series.forEach(p => rows.push([p.timestamp, p.fused_score]))
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
  await loadDeathVectors()
  await loadDetections()
}

window.addEventListener('load', () => {
  initMap()
  refreshAll()
  // Wire CSV download
  document.getElementById('downloadCsv').addEventListener('click', async () => {
    const h = await fetchJson(API_ROOT + '/history')
    downloadCSV(h.series)
  })
  // Wire focus latest RED button
  const focusBtn = document.getElementById('focusLatestRed')
  if (focusBtn) focusBtn.addEventListener('click', focusLatestRed)
  // Refresh every 10s
  setInterval(refreshAll, 10000)
})
