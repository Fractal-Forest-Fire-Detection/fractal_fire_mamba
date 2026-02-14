// --- Chart.js Minimalist Defaults (Government Theme) ---
Chart.defaults.color = '#1d1b1a'; // Dark text for white background
Chart.defaults.borderColor = '#b1b4b6';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.plugins.legend.display = false;

const chartScaleOpts = {
  grid: { color: '#e5e7eb', drawBorder: false },
  ticks: { font: { size: 11 } }
};

// --- Global State ---
let selectedNodeDetails = null; // Stores currently selected Queen for detail view


const API_ROOT = '/api';
let hasAutoTriggeredSatellite = false; // Prevent multiple auto-triggers

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

  // OVERRIDE: If a node is selected, show IT's specific scores instead
  if (selectedNodeDetails) {
    const nd = selectedNodeDetails;
    if (nd.chem_score !== undefined) {
      document.getElementById('scoreChem').textContent = nd.chem_score.toFixed(2);
      document.getElementById('barChem').style.width = (nd.chem_score * 100) + '%';
    }
    if (nd.vis_score !== undefined) {
      document.getElementById('scoreVis').textContent = nd.vis_score.toFixed(2);
      document.getElementById('barVis').style.width = (nd.vis_score * 100) + '%';
    }
    if (nd.env_score !== undefined) {
      document.getElementById('scoreEnv').textContent = nd.env_score.toFixed(2);
      document.getElementById('barEnv').style.width = (nd.env_score * 100) + '%';
    }
  }
}

// --- Node Selection Logic ---
window.selectQueen = function (nodeId) {
  // Find node data from global mesh cache (we need to access it)
  // Since we don't have global mesh ref easily here relative to loop, 
  // we'll rely on the fact that click handlers are rebuilt every frame 
  // with the LATEST data closure if we do it right, OR we store mesh globally.
  // Better: we store the node object directly in the DOM element OR lookup.
  // Actually, let's just use the ID and find it in the next render cycle or use a global lookup.

  // For simplicity: toggle selection
  if (selectedNodeDetails && selectedNodeDetails.id === nodeId) {
    selectedNodeDetails = null; // Deselect
    document.getElementById('nodeTelemetryContainer').style.display = 'none';
  } else {
    // We need the actual node object. 
    // We'll trust that the UI render loop will update 'selectedNodeDetails' content 
    // if we just store the ID, but here we want immediate feedback.
    // Let's store just the ID for now and let renderQueenHealth update the details object.
    selectedNodeDetails = { id: nodeId }; // Placeholder until next frame updates it full
    document.getElementById('nodeTelemetryContainer').style.display = 'block';
  }

  // Trigger immediate re-render if possible (not needed if 1s loop)
  // console.log("Selected Node:", nodeId);
}

function renderNodeTelemetry(node) {
  const container = document.getElementById('nodeTelemetryContent');
  const panel = document.getElementById('nodeTelemetryContainer');
  if (!container || !panel) return;

  if (!node) {
    panel.style.display = 'none';
    return;
  }

  panel.style.display = 'block';

  // Safety check for sensor data
  const sensors = node.sensors || {};
  const bme = sensors.bme688 || {};
  const soil = sensors.capacitive_soil || {};
  const power = node.power || {};
  const bat = power.battery || {};

  container.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.75rem;">
            <!-- Environmental -->
            <div class="metric-box" style="background:var(--light-bg); padding:6px; border-radius:4px;">
                <div style="color:#666;">Humidity</div>
                <div style="font-size:1rem; font-weight:bold; color:var(--deep-blue);">
                    ${bme.humidity_pct ? bme.humidity_pct.toFixed(1) + '%' : '--'}
                </div>
            </div>
             <div class="metric-box" style="background:var(--light-bg); padding:6px; border-radius:4px;">
                <div style="color:#666;">Soil Moisture</div>
                <div style="font-size:1rem; font-weight:bold; color:var(--warning);">
                    ${soil.moisture_pct ? soil.moisture_pct.toFixed(1) + '%' : '--'}
                </div>
            </div>
            
            <!-- Power -->
            <div class="metric-box" style="background:var(--light-bg); padding:6px; border-radius:4px;">
                <div style="color:#666;">Battery Volts</div>
                <div>${bat.voltage_v ? bat.voltage_v + 'V' : '--'}</div>
            </div>
            <div class="metric-box" style="background:var(--light-bg); padding:6px; border-radius:4px;">
                <div style="color:#666;">Temp</div>
                <div>${bme.temp_c ? bme.temp_c + '°C' : '--'}</div>
            </div>
        </div>
        <div style="margin-top:6px; font-size:0.7rem; color:#888;">
            ID: ${node.id} &bull; ROLE: ${node.role}
        </div>
    `;
}

// Map Logic
let map = null;
let nodeMarker = null;
let detectionMarkers = {};
let deathVectorLayers = []; // Layers for spread vectors

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

async function updateDeathVectors() {
  if (!map) return;
  try {
    const data = await fetchJson(API_ROOT + '/death_vectors');
    const vectors = data.vectors || [];

    // Clear old vector layers
    deathVectorLayers.forEach(l => map.removeLayer(l));
    deathVectorLayers = [];

    vectors.forEach(v => {
      const start = [v.start.latitude, v.start.longitude];
      const end = [v.end.latitude, v.end.longitude];
      const color = v.risk_level === 'CRITICAL' ? '#d4351c' : '#f47738';

      // 1. Draw the polyline with a dashed pattern and glow
      const poly = L.polyline([start, end], {
        color: color,
        weight: 4,
        opacity: 0.7,
        dashArray: '10, 10'
      }).addTo(map);

      // 2. Add an arrowhead or label for direction
      const label = L.tooltip({
        permanent: true,
        direction: 'right',
        className: 'vector-label',
        opacity: 0.9
      })
        .setContent(`<span style="background:${color}; color:white; padding:2px 6px; border-radius:3px; font-size:10px;">${v.label}</span>`)
        .setLatLng(end)
        .addTo(map);

      deathVectorLayers.push(poly);
      deathVectorLayers.push(label);
    });
  } catch (e) {
    console.warn("Death vectors load failed", e);
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

    // --- AUTO-TRIGGER SATELLITE ANALYSIS (Phase 4/5 Escalation) ---
    if (s.fire_detected && !hasAutoTriggeredSatellite) {
      const btnSat = document.getElementById('btnSatTrigger');
      const modal = document.getElementById('satModal');
      // Only trigger if modal isn't already open
      if (btnSat && modal && modal.style.display !== 'block') {
        console.log("🚀 [AUTO-THREAT] Red Alert confirmed. Initiating Satellite Uplink...");
        hasAutoTriggeredSatellite = true;
        btnSat.click();
      }
    }

    // Reset if system goes back to nominal
    if (!s.fire_detected && s.risk_tier === 'NOMINAL') {
      hasAutoTriggeredSatellite = false;
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
    const color = a.level === 'RED' ? '#d4351c' : a.level === 'ORANGE' ? '#f47738' : '#00703c';
    const levelText = a.level === 'GREEN' ? 'NOMINAL' : a.level;
    li.innerHTML = `<strong style="color:${color}">${levelText}</strong> <span style="color:#505a5f; font-size:0.9em;">(${time})</span> Score: ${a.score}`
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

    // Update LoRa Link Quality panel
    renderLoraLinks(mesh)

    // Update SBD Outbound Queue
    renderSbdQueue(mesh)
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
    marker.on('click', () => selectQueen(q.id))
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
    if (d.queen_id) {
      marker.on('click', () => selectQueen(d.queen_id))
    }
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

  // LoRa Range Circles (5km radius) around each Queen
  nodes.filter(n => n.is_queen).forEach(q => {
    const circle = L.circle([q.lat, q.lon], {
      radius: 5000,  // 5km LoRa range
      color: '#3b82f6',
      fillColor: '#3b82f6',
      fillOpacity: 0.04,
      weight: 1,
      dashArray: '6 4',
      interactive: false
    }).addTo(map)
    meshLines.push(circle)

    // Label for range circle
    const label = L.tooltip({
      permanent: true,
      direction: 'bottom',
      className: 'lora-range-label',
      offset: [0, 45]
    })
      .setContent(`<span style="font-size:9px; color:#3b82f6; background:rgba(255,255,255,0.85); padding:1px 4px; border-radius:2px;">LoRa 5km</span>`)
      .setLatLng([q.lat, q.lon])
      .addTo(map)
    meshLines.push(label)
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

  // ── Drones (blue, smaller) ──
  drones.forEach(d => {
    const pos = positions[d.id]
    if (!pos) return;

    const riskColor = d.risk_score > 0.7 ? '#ef4444' : d.risk_score > 0.4 ? '#f97316' : '#3b82f6'

    // Outer ring
    ctx.strokeStyle = riskColor
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.arc(pos.x, pos.y, 8, 0, Math.PI * 2)
    ctx.stroke()

    // Fill
    ctx.fillStyle = '#ffffff'
    ctx.beginPath()
    ctx.arc(pos.x, pos.y, 6, 0, Math.PI * 2)
    ctx.fill()

    // Label
    ctx.fillStyle = '#334155'
    ctx.font = '9px Inter, system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    // Show just the number suffix (e.g. "01")
    const shortLabel = d.id.split('_').pop()
    ctx.fillText(shortLabel, pos.x, pos.y + 0.5)

    // ID Label below
    // ctx.fillStyle = '#64748b'
    // ctx.font = '8px Inter, system-ui, sans-serif'
    // ctx.fillText(d.id.replace('D_',''), pos.x, pos.y + 14)
  })

  // ── Queens (gold, larger) ──
  queens.forEach(q => {
    const pos = positions[q.id]
    if (!pos) return;

    // Glow effect
    const gradient = ctx.createRadialGradient(pos.x, pos.y, 8, pos.x, pos.y, 16)
    gradient.addColorStop(0, 'rgba(251, 191, 36, 0.4)')
    gradient.addColorStop(1, 'rgba(251, 191, 36, 0)')
    ctx.fillStyle = gradient
    ctx.beginPath()
    ctx.arc(pos.x, pos.y, 16, 0, Math.PI * 2)
    ctx.fill()

    // Circle
    ctx.fillStyle = '#f59e0b'
    ctx.beginPath()
    ctx.arc(pos.x, pos.y, 10, 0, Math.PI * 2)
    ctx.fill()

    // Crown Icon (simple text)
    ctx.fillStyle = '#ffffff'
    ctx.font = '12px Inter'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('👑', pos.x, pos.y + 1)

    // Label
    ctx.fillStyle = '#1e293b'
    ctx.font = 'bold 10px Inter, system-ui, sans-serif'
    ctx.fillText(q.id.replace('QUEEN_', 'QN-'), pos.x, pos.y + 18)
  })
}

// ==========================================================================
// SATELLITE ANALYTICS LOGIC (Mamba vs CNN)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  // Modal Elements
  const modal = document.getElementById('satModal');
  const btnTrigger = document.getElementById('btnSatTrigger');
  const spanClose = document.getElementsByClassName("close-modal")[0];

  if (btnTrigger) {
    btnTrigger.onclick = async function () {
      // 1. Show Modal immediately with loading state
      modal.style.display = "block";
      resetSatModal();

      // 2. Pick a random satellite image from the known list
      // (In a real app, this would be a file upload or live feed)
      const demoImages = [
        "5e0e57c4855cc20ccc748d04-1200.jpg",
        "_111122060_2.jpg.webp", // Smoke
        "BAtUskUTVVBLb2hckveHng-720-80.jpg" // Another available image
      ];
      const randomImg = demoImages[Math.floor(Math.random() * demoImages.length)];

      // 3. Call Backend API
      try {
        const response = await fetch(API_ROOT + '/satellite/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_filename: randomImg })
        });
        const data = await response.json();

        // 4. Update UI with results
        updateSatModal(data);

      } catch (e) {
        console.error("Satellite Analysis Failed:", e);
        alert("Satellite Uplink Failed: " + e.message);
      }
    }
  }

  if (spanClose) {
    spanClose.onclick = function () {
      modal.style.display = "none";
    }
  }

  window.onclick = function (event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
  }
});

function resetSatModal() {
  document.getElementById('satImage').src = "";
  document.getElementById('satTimestamp').textContent = "Acquiring Signal...";

  // Reset Bars
  document.getElementById('cnnBar').style.width = "0%";
  document.getElementById('cnnTime').textContent = "--s";
  document.getElementById('cnnConf').textContent = "--%";

  document.getElementById('mambaBar').style.width = "0%";
  document.getElementById('mambaTime').textContent = "--s";
  document.getElementById('mambaConf').textContent = "--%";

  document.getElementById('satAlertBox').style.display = 'none';
  document.getElementById('speedupFactor').textContent = "Calculatng...";
}

function updateSatModal(data) {
  if (data.error) {
    alert(data.error);
    return;
  }

  // Image
  const imgUrl = `/api/images/${data.image_path.split('/').pop()}`; // Hacky path fix
  document.getElementById('satImage').src = imgUrl;
  document.getElementById('satTimestamp').textContent = "Timestamp: " + new Date(data.timestamp).toLocaleString();

  // CNN Stats
  document.getElementById('cnnTime').textContent = data.cnn.duration_sec.toFixed(3) + "s";
  document.getElementById('cnnPower').textContent = data.cnn.power_est_watts + "W";
  document.getElementById('cnnConf').textContent = (data.cnn.confidence * 100).toFixed(1) + "%";
  document.getElementById('cnnBar').style.width = (data.cnn.confidence * 100) + "%";

  // Mamba Stats
  document.getElementById('mambaTime').textContent = data.mamba.duration_sec.toFixed(3) + "s";
  document.getElementById('mambaPower').textContent = data.mamba.power_est_watts + "W";
  document.getElementById('mambaConf').textContent = (data.mamba.confidence * 100).toFixed(1) + "%";
  document.getElementById('mambaBar').style.width = (data.mamba.confidence * 100) + "%";

  // Speedup
  document.getElementById('speedupFactor').textContent = data.speedup_factor + "x";

  // Alert Box?
  if (data.mamba.confidence > 0.6) {
    document.getElementById('satAlertBox').style.display = 'block';
    // Auto-Focus Map to new location (handled by global state polling, but we can force it here visually too)
  }
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
      <div onclick="selectQueen('${q.id}')" 
           style="cursor: pointer; padding: 8px; margin-bottom: 8px; background: ${q.id === (selectedNodeDetails?.id) ? '#e0f2fe' : 'var(--light-bg)'}; border-radius: 4px; border-left: 3px solid ${healthColor}; border: ${q.id === (selectedNodeDetails?.id) ? '2px solid #3b82f6' : 'none'}; border-left: 3px solid ${healthColor};">
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

  // Update Telemetry Panel if a node is selected
  if (selectedNodeDetails && selectedNodeDetails.id) {
    const target = queens.find(q => q.id === selectedNodeDetails.id);
    if (target) {
      selectedNodeDetails = target; // Update with latest data
      renderNodeTelemetry(target);
    }
  }

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

// ==========================================================================
// LORA LINK QUALITY PANEL
// ==========================================================================

function renderLoraLinks(mesh) {
  const container = document.getElementById('loraLinkList')
  if (!container) return;

  const links = (mesh.links || []).filter(l => l.type === 'lora')
  if (links.length === 0) {
    container.innerHTML = '<p style="color:#999; font-size:0.72rem;">No LoRa links active</p>'
    return
  }

  container.innerHTML = links.map(l => {
    const rssi = l.rssi_dbm || -80
    const snr = l.snr_db || 5
    const dist = l.distance_m || 0

    // Signal strength: green > -70, yellow > -90, red <= -90
    let sigColor = '#16a34a'
    let sigLabel = 'STRONG'
    if (rssi < -90) { sigColor = '#dc2626'; sigLabel = 'WEAK' }
    else if (rssi < -70) { sigColor = '#f59e0b'; sigLabel = 'FAIR' }

    // Bar width (0-100%) mapped from RSSI range -120 to -30
    const barPct = Math.max(0, Math.min(100, ((rssi + 120) / 90) * 100))

    const shortSrc = l.source.replace('D_', '').replace('_0', '-')
    const shortTgt = l.target.replace('QUEEN_', 'Q:')

    return `<div style="display: flex; align-items: center; gap: 4px; padding: 2px 0; border-bottom: 1px solid #f0f0f0;">
      <span style="width: 60px; font-weight: 500; color: #334155;">${shortSrc}</span>
      <div style="flex: 1; background: #e2e8f0; border-radius: 2px; height: 6px; position: relative;">
        <div style="width: ${barPct}%; background: ${sigColor}; height: 100%; border-radius: 2px;"></div>
      </div>
      <span style="width: 50px; text-align: right; color: ${sigColor}; font-weight: 600;">${rssi} dBm</span>
      <span style="width: 38px; text-align: right; color: #64748b;">SNR ${snr}</span>
    </div>`
  }).join('')
}

// ==========================================================================
// IRIDIUM SBD MESSAGE QUEUE
// ==========================================================================

function renderSbdQueue(mesh) {
  const container = document.getElementById('sbdQueue')
  if (!container) return;

  const queue = mesh.sbd_queue || []
  if (queue.length === 0) {
    container.innerHTML = '<p style="color:#999;">No messages queued</p>'
    return
  }

  container.innerHTML = queue.map(msg => {
    // Priority badge
    const priColor = msg.priority === 'CRITICAL' ? '#dc2626' : '#64748b'
    const priBg = msg.priority === 'CRITICAL' ? '#fef2f2' : '#f8fafc'

    // Status badge
    let statusColor = '#16a34a', statusBg = '#f0fdf4'
    if (msg.status === 'PENDING') { statusColor = '#f59e0b'; statusBg = '#fffbeb' }
    else if (msg.status === 'QUEUED') { statusColor = '#6366f1'; statusBg = '#eef2ff' }

    const shortQueen = msg.queen.replace('QUEEN_', '')

    return `<div style="display: flex; align-items: center; gap: 4px; padding: 3px 0; border-bottom: 1px solid #f0f0f0;">
      <span style="font-weight: 600; color: ${priColor}; background: ${priBg}; padding: 0 4px; border-radius: 2px; font-size: 0.65rem;">${msg.type}</span>
      <span style="color: #475569; flex: 1;">${shortQueen}</span>
      <span style="color: #94a3b8;">${msg.size_bytes}B</span>
      <span style="color: ${statusColor}; background: ${statusBg}; padding: 0 4px; border-radius: 2px; font-weight: 600; font-size: 0.65rem;">${msg.status}</span>
    </div>`
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
  await updateDeathVectors()
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