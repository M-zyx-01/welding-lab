// Welding Intelligence Lab - Frontend Application
const API = "/api";
let currentResults = null, currentInference = null;
let currentLang = "zh";
let peakTempChart = null, sensitivityChart = null;
let compareScenarios = [];

function setLang(lang) {
  currentLang = lang;
  document.querySelectorAll(".lang-btn").forEach(function(b) { b.classList.toggle("active", b.dataset.lang === lang); });
  document.getElementById("toolbar-subtitle").textContent =
    lang === "zh" ? "多物理场焊接智能分析平台" : "Multi-Physics Welding Intelligence Platform";
}

document.addEventListener("DOMContentLoaded", function() {
  loadMaterials();
  loadEnvironments();
  setupTabs();
  setupLangToggle();
  setupProcessDefaults();
  setupFeatureClick();
});

function setupLangToggle() {
  document.querySelectorAll(".lang-btn").forEach(function(btn) {
    btn.addEventListener("click", function() { setLang(btn.dataset.lang); });
  });
}

function setupFeatureClick() {
  document.querySelectorAll(".feature[data-nav]").forEach(function(f) {
    f.addEventListener("click", function() {
      if (!currentResults && !currentInference) {
        showStatus("请先运行分析 Run analysis first", "error");
        return;
      }
      var tabId = f.dataset.nav;
      var tab = document.querySelector('.tab[data-tab="' + tabId + '"]');
      if (tab) tab.click();
    });
  });
}

function setupProcessDefaults() {
  var defaults = {
    GTAW: {efficiency:0.70, electrode:2.4},
    GMAW: {efficiency:0.80, electrode:1.2},
    SMAW: {efficiency:0.75, electrode:3.2},
    FCAW: {efficiency:0.80, electrode:1.6},
    SAW: {efficiency:0.95, electrode:4.0},
    PAW: {efficiency:0.75, electrode:3.0},
    LBW: {efficiency:0.85, electrode:0.3},
    EBW: {efficiency:0.90, electrode:0.5}
  };
  document.getElementById("sel-process").addEventListener("change", function(e) {
    var d = defaults[e.target.value];
    if (d) {
      document.getElementById("inp-efficiency").value = d.efficiency;
      document.getElementById("inp-electrode").value = d.electrode;
    }
  });
}

async function loadMaterials() {
  try {
    var res = await fetch(API + "/materials");
    var data = await res.json();
    var mats = data.materials;
    var selBase = document.getElementById("sel-base-mat");
    var selFiller = document.getElementById("sel-filler-mat");
    var sorted = Object.entries(mats).sort(function(a, b) {
      var catOrder = {carbon_steel:1, stainless_steel:2, aluminium:3, nickel:4, titanium:5, copper:6};
      return (catOrder[a[1].category] || 9) - (catOrder[b[1].category] || 9);
    });
    sorted.forEach(function(entry) {
      var key = entry[0], mat = entry[1];
      var ymp = mat.yield_strength_MPa || 0;
      var label = mat.name + (mat.grade ? " (" + mat.grade + ")" : "") + " - " + ymp + " MPa";
      var opt = document.createElement("option");
      opt.value = key;
      opt.textContent = label;
      selBase.appendChild(opt);
      selFiller.appendChild(opt.cloneNode(true));
    });
  } catch (e) {
    showStatus("Failed to load materials: " + e.message, "error");
  }
}

async function loadEnvironments() {
  try {
    var res = await fetch(API + "/environments");
    var data = await res.json();
    var sel = document.getElementById("sel-environment");
    data.environments.forEach(function(env) {
      var opt = document.createElement("option");
      opt.value = env.key;
      opt.textContent = (env.name_cn || env.name) + " / " + env.name;
      opt.title = env.description || "";
      sel.appendChild(opt);
    });
  } catch (e) {
    showStatus("Failed to load environments: " + e.message, "error");
  }
}

function gatherInput() {
  var fmk = document.getElementById("sel-filler-mat").value;
  return {
    id: "weld-" + Date.now(),
    base_material_key: document.getElementById("sel-base-mat").value || "Q345",
    filler_material_key: fmk || null,
    parameters: {
      process: document.getElementById("sel-process").value,
      current: parseFloat(document.getElementById("inp-current").value) || 150,
      voltage: parseFloat(document.getElementById("inp-voltage").value) || 20,
      travel_speed: parseFloat(document.getElementById("inp-speed").value) || 2,
      arc_efficiency: parseFloat(document.getElementById("inp-efficiency").value) || 0.75,
      electrode_diameter: parseFloat(document.getElementById("inp-electrode").value) || 2.4,
      torch_angle: parseFloat(document.getElementById("inp-torch-angle").value) || 90,
      travel_angle: parseFloat(document.getElementById("inp-travel-angle").value) || 0,
      arc_length: parseFloat(document.getElementById("inp-arc-length").value) || 3,
      polarity: document.getElementById("sel-polarity").value,
      preheat_temp: parseFloat(document.getElementById("inp-preheat").value) || 25,
      interpass_temp: parseFloat(document.getElementById("inp-interpass").value) || 150
    },
    joint: {
      joint_type: document.getElementById("sel-joint-type").value,
      position: document.getElementById("sel-position").value,
      plate_thickness: parseFloat(document.getElementById("inp-thickness").value) || 10,
      bevel_angle: parseFloat(document.getElementById("inp-bevel").value) || 30,
      groove_type: document.getElementById("sel-groove").value,
      number_of_passes: parseInt(document.getElementById("inp-passes").value) || 3
    },
    environment: document.getElementById("sel-environment").value || "indoor_standard"
  };
}

function showResults() {
  document.getElementById("empty-state").classList.add("hidden");
  document.getElementById("results-container").classList.remove("hidden");
}

function showStatus(msg, type) {
  var el = document.getElementById("status");
  el.textContent = msg;
  el.className = "status show " + (type || "loading");
  if (type === "success") setTimeout(function() { el.classList.remove("show"); }, 3000);
}

function renderQualityBar(q) {
  var grade = q.grade || "?";
  var score = q.quality_score || 0;
  var bar = document.getElementById("quality-bar");
  bar.className = "quality-bar grade-" + grade;
  bar.innerHTML = '<span class="quality-grade">' + grade + '</span><div><div style="font-size:14px">质量分数 Quality Score: ' + score + ' / 100</div><div style="font-size:11px;color:var(--text2);margin-top:2px">风险评估 Risk: ' + (q.risk_assessment || "N/A") + '</div></div>';
}

function setActiveTab(tabId) {
  document.querySelectorAll(".tab").forEach(function(t) { t.classList.remove("active"); });
  document.querySelectorAll(".tab-panel").forEach(function(p) { p.classList.remove("active"); });
  var tab = document.querySelector('.tab[data-tab="' + tabId + '"]');
  if (tab) tab.classList.add("active");
  var panel = document.getElementById(tabId);
  if (panel) {
    panel.classList.add("active");
    if (tabId === "tab-thermal" && currentResults) setTimeout(function() { drawPeakTempChart(currentResults.thermal); }, 150);
  }
}

async function runAnalysis() {
  showStatus("Running full analysis...", "loading");
  var input = gatherInput();
  try {
    var res = await fetch(API + "/analyze", {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(input)
    });
    var data = await res.json();
    currentResults = data;
    showResults();
    renderQualityBar(data.quality || {});
    renderAllTabs(data);
    setActiveTab("tab-summary");
    showStatus("Analysis complete", "success");
  } catch (e) {
    showStatus("Analysis failed: " + e.message, "error");
  }
}

async function runInference() {
  showStatus("Running cross-domain inference...", "loading");
  var input = gatherInput();
  try {
    var res = await fetch(API + "/inference", {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(input)
    });
    var data = await res.json();
    currentInference = data;
    if (!currentResults) showResults();
    renderInferenceTab(data);
    setActiveTab("tab-inference");
    showStatus("Inference complete", "success");
  } catch (e) {
    showStatus("Inference failed: " + e.message, "error");
  }
}

async function runQuickCheck() {
  showStatus("Running quick check...", "loading");
  var input = gatherInput();
  try {
    var res = await fetch(API + "/quick", {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(input)
    });
    var data = await res.json();
    showStatus("Quick check: Score " + data.quality_score + " / Grade " + data.grade, "success");
  } catch (e) {
    showStatus("Quick check failed: " + e.message, "error");
  }
}

async function generateReport() {
  showStatus("Generating report...", "loading");
  var input = gatherInput();
  var params = new URLSearchParams({
    base_material_key: input.base_material_key,
    filler_material_key: input.filler_material_key || "",
    process: input.parameters.process,
    current: input.parameters.current,
    voltage: input.parameters.voltage,
    travel_speed: input.parameters.travel_speed,
    joint_type: input.joint.joint_type,
    plate_thickness: input.joint.plate_thickness,
    environment: input.environment
  });
  try {
    var res = await fetch(API + "/report?" + params.toString());
    var data = await res.json();
    document.getElementById("report-body").textContent = data.report;
    document.getElementById("report-modal").classList.remove("hidden");
    showStatus("Report ready", "success");
  } catch (e) {
    showStatus("Report failed: " + e.message, "error");
  }
}

async function runSensitivity() {
  showStatus("Running auto-sensitivity...", "loading");
  var input = gatherInput();
  try {
    var res = await fetch(API + "/auto-sensitivity", {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(input)
    });
    var data = await res.json();
    if (!currentResults) showResults();
    renderSensitivityTab(data);
    setActiveTab("tab-sensitivity");
    showStatus("Sensitivity analysis complete", "success");
  } catch (e) {
    showStatus("Sensitivity failed: " + e.message, "error");
  }
}

async function saveScenario() {
  var input = gatherInput();
  try {
    var res = await fetch(API + "/scenarios/save", {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(input)
    });
    var data = await res.json();
    showStatus("Saved: " + data.filename, "success");
  } catch (e) {
    showStatus("Save failed: " + e.message, "error");
  }
}

async function toggleScenarios() {
  showStatus("Loading saved scenarios...", "loading");
  try {
    var res = await fetch(API + "/scenarios");
    var data = await res.json();
    var list = data.scenarios || [];
    if (!list.length) { showStatus("No saved scenarios found", "error"); return; }
    alert("Saved scenarios:\n" + list.join("\n"));
    showStatus(list.length + " scenario(s) found", "success");
  } catch (e) {
    showStatus("Load failed: " + e.message, "error");
  }
}

async function toggleCompare() {
  var input = gatherInput();
  compareScenarios.push(input);
  if (compareScenarios.length < 2) {
    showStatus("Added scenario " + compareScenarios.length + ". Add one more to compare.", "loading");
    return;
  }
  showStatus("Running comparison (" + compareScenarios.length + " scenarios)...", "loading");
  try {
    var res = await fetch(API + "/compare", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ scenarios: compareScenarios })
    });
    var data = await res.json();
    if (!currentResults) showResults();
    renderCompareTab(data);
    setActiveTab("tab-compare");
    compareScenarios = [];
    showStatus("Comparison complete", "success");
  } catch (e) {
    compareScenarios = [];
    showStatus("Compare failed: " + e.message, "error");
  }
}

function toggleBatch() {
  document.getElementById("batch-modal").classList.remove("hidden");
}

function closeBatch() {
  document.getElementById("batch-modal").classList.add("hidden");
}

async function runBatchCSV() {
  var csv = document.getElementById("batch-csv").value;
  if (!csv.trim()) { showStatus("请粘贴CSV数据 Paste CSV data first", "error"); return; }
  showStatus("Running batch...", "loading");
  try {
    var res = await fetch(API + "/batch-csv", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ csv_data: csv })
    });
    var data = await res.json();
    showStatus("Batch complete: " + data.count + " scenarios", "success");
    closeBatch();
  } catch (e) {
    showStatus("Batch failed: " + e.message, "error");
  }
}

function card(label, value) {
  return '<div class="info-card"><div class="label">' + label + '</div><div class="value">' + value + '</div></div>';
}

function renderAllTabs(data) {
  var q = data.quality || {};
  var a = data.analysis || {};
  var summary = a.summary || {};

  // Summary tab
  var s = '<div class="info-grid">';
  s += card("材料 Material", summary.base_material || "N/A");
  s += card("工艺 Process", summary.weld_process || "N/A");
  s += card("质量分数 Score", q.quality_score + " / 100");
  s += card("质量等级 Grade", q.grade || "N/A");
  s += card("综合风险 Risk", summary.overall_risk || "N/A");
  s += card("焊接性 Weldability", summary.weldability || "N/A");
  s += '</div>';
  var recs = summary.recommendations || [];
  if (recs.length) {
    s += '<h4 style="margin:12px 0 8px;color:var(--text2)">建议 Recommendations</h4><ul class="recommendation-list">';
    recs.forEach(function(r) { s += '<li>' + r + '</li>'; });
    s += '</ul>';
  }
  document.getElementById("tab-summary").innerHTML = s;

  // Material tab
  renderDomainTab("tab-material", a.material || {}, "材料分析 Material Analysis");

  // Thermal tab
  var t = a.thermal || {};
  var th = '<div class="info-grid">';
  th += card("峰值温度 Peak Temp", (t.peak_temperature_C || "N/A") + " C");
  th += card("冷却速率 Cooling Rate", (t.cooling_rate_C_per_s || "N/A") + " C/s");
  th += card("热输入 Heat Input", (t.heat_input_kJ_mm || "N/A") + " kJ/mm");
  th += card("HAZ宽度 HAZ Width", (t.haz_width_mm || "N/A") + " mm");
  th += card("预热 Preheat", (t.recommended_preheat_C || t.preheat_temp || "N/A") + " C");
  th += card("层间 Interpass", (t.interpass_temp || "N/A") + " C");
  th += '</div>';
  if (t.peak_temperatures && t.peak_temperatures.length) {
    th += '<div class="chart-container" style="margin-top:10px;height:280px"><canvas id="chart-peak-temp"></canvas></div>';
  }
  document.getElementById("tab-thermal").innerHTML = th;
  if (t.peak_temperatures) setTimeout(function() { drawPeakTempChart(t); }, 200);

  // Mechanical tab
  renderDomainTab("tab-mechanical", a.mechanical || {}, "力学分析 Mechanical Analysis");

  // Fluid tab
  renderDomainTab("tab-fluid", a.fluid || a.fluid_dynamics || {}, "流体分析 Fluid Dynamics");

  // EM tab
  renderDomainTab("tab-em", a.electromagnetic || a.em || {}, "电磁分析 EM Analysis");

  // Environmental tab
  var env = a.environmental || {};
  var eh = '<div class="info-grid">';
  var envKeys = ["corrosion_rate_mm_per_year", "estimated_service_life_years", "corrosion_risk", "fatigue_limit_MPa", "fatigue_life_years", "hicc_risk", "risk_score", "environment"];
  envKeys.forEach(function(k) {
    if (env[k] !== undefined) {
      var label = k.replace(/_/g, " ").replace(/\b\w/g, function(c) { return c.toUpperCase(); });
      var val = typeof env[k] === "number" ? (Number.isInteger(env[k]) ? env[k] : env[k].toFixed(2)) : String(env[k]);
      eh += card(label, val);
    }
  });
  eh += '</div>';
  var envRecs = env.recommendations || env.mitigations || [];
  if (envRecs.length) {
    eh += '<h4 style="margin:12px 0 8px;color:var(--text2)">环境建议 Environmental Recommendations</h4><ul class="recommendation-list">';
    envRecs.forEach(function(r) { eh += '<li>' + r + '</li>'; });
    eh += '</ul>';
  }
  document.getElementById("tab-env").innerHTML = eh;
}

function renderDomainTab(id, domain, title) {
  var h = '<div class="info-grid">';
  Object.entries(domain).forEach(function(entry) {
    var k = entry[0], v = entry[1];
    if (typeof v === "object" || k === "peak_temperatures" || k === "detailed_sweeps") return;
    var label = k.replace(/_/g, " ").replace(/\b\w/g, function(c) { return c.toUpperCase(); });
    var val = typeof v === "number" ? (Number.isInteger(v) ? v : v.toFixed(2)) : String(v);
    h += card(label, val);
  });
  h += '</div>';
  document.getElementById(id).innerHTML = h;
}

function renderInferenceTab(data) {
  var inferences = data.inferences || data.cross_domain_inferences || [];
  var h = '<h3 style="margin-bottom:8px">跨领域推理 Cross-Domain Inference</h3>';
  if (!inferences.length) {
    h += '<p style="color:var(--text2)">暂无推理结果 No inference results available.</p>';
  } else {
    inferences.forEach(function(inf) {
      h += '<div class="inference-card">';
      h += '<div class="i-domain">' + (inf.domain || inf.type || "Inference") + '</div>';
      h += '<div class="i-finding">' + (inf.finding || inf.description || "") + '</div>';
      h += '<div class="i-rec">' + (inf.implication || inf.recommendation || "") + '</div>';
      h += '</div>';
    });
  }
  document.getElementById("tab-inference").innerHTML = h;
}

function renderSensitivityTab(data) {
  var rankings = data.sensitivity_ranking || data.rankings || [];
  var h = '<h3 style="margin-bottom:8px">参数敏感性分析 Sensitivity Analysis</h3>';
  if (rankings.length) {
    h += '<div class="info-grid">';
    rankings.forEach(function(r) {
      h += '<div class="info-card"><div class="label">' + r.parameter + '</div>';
      h += '<div class="value">' + (r.impact_score || r.score || 0).toFixed(1) + ' pts</div>';
      h += '<div class="sub">' + (r.interpretation || "") + '</div></div>';
    });
    h += '</div>';
  }
  if (data.detailed_sweeps || data.sweeps) {
    h += '<div class="chart-container" style="margin-top:10px;height:300px"><canvas id="chart-sensitivity"></canvas></div>';
  }
  document.getElementById("tab-sensitivity").innerHTML = h;
  if (data.detailed_sweeps || data.sweeps) setTimeout(function() { drawSensitivityChart(data); }, 200);
}

function renderCompareTab(data) {
  var sc = data.scenarios || [];
  var h = '<h3 style="margin-bottom:10px">情景对比 Comparison (' + sc.length + ' scenarios)</h3>';
  h += '<div style="overflow-x:auto"><table class="comp-table"><thead><tr>';
  h += '<th>#</th><th>材料 Material</th><th>工艺 Process</th><th>环境 Env</th><th>分数 Score</th><th>等级 Grade</th><th>HAZ</th><th>应力 Stress</th><th>腐蚀 Corr</th><th>寿命 Life</th><th>风险 Risk</th>';
  h += '</tr></thead><tbody>';
  var bi = data.comparison ? (data.comparison.best_scenario || {}).index : -1;
  var wi = data.comparison ? (data.comparison.worst_scenario || {}).index : -1;
  sc.forEach(function(s, i) {
    var cls = i === bi ? "best" : (i === wi ? "worst" : "");
    h += '<tr class="' + cls + '"><td>' + (i + 1) + '</td>';
    h += '<td>' + (s.material || "") + '</td><td>' + (s.process || "") + '</td><td>' + (s.environment || "") + '</td>';
    h += '<td><strong>' + (s.quality_score || 0) + '</strong></td><td>' + (s.quality_grade || "") + '</td>';
    h += '<td>' + (s.haz_width_mm || "") + '</td><td>' + Math.round(s.residual_stress_MPa || 0) + '</td>';
    h += '<td>' + (s.corrosion_rate_mm_per_yr || "") + '</td><td>' + Math.round(s.service_life_years || 0) + '</td>';
    h += '<td><span class="risk-badge risk-' + ((s.overall_risk || "low").toLowerCase().replace(/ /g, "-")) + '">' + (s.overall_risk || "") + '</span></td></tr>';
  });
  h += '</tbody></table></div>';
  if (data.comparison && data.comparison.trade_off_analysis && data.comparison.trade_off_analysis.length) {
    h += '<h4 style="margin-top:12px">权衡分析 Trade-off</h4>';
    data.comparison.trade_off_analysis.forEach(function(t) {
      h += '<div class="inference-card"><div class="i-domain">' + (t.type || "") + '</div>';
      h += '<div class="i-finding">' + (t.finding || t.finding_cn || "") + '</div>';
      h += '<div class="i-rec">' + (t.implication || t.implication_cn || "") + '</div></div>';
    });
  }
  document.getElementById("tab-compare").innerHTML = h;
}

// Charts
function drawPeakTempChart(t) {
  var canvas = document.getElementById("chart-peak-temp");
  if (!canvas) return;
  if (peakTempChart) peakTempChart.destroy();
  var pts = (t && t.peak_temperatures) ? t.peak_temperatures : [];
  if (!pts.length) return;
  peakTempChart = new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels: pts.map(function(p) { return (p.distance_from_center_mm || 0) + " mm"; }),
      datasets: [{
        label: "峰值温度 Peak Temp (C)",
        data: pts.map(function(p) { return p.peak_temperature_C || 0; }),
        borderColor: "#e74c3c",
        backgroundColor: "rgba(231,76,60,0.1)",
        fill: true, tension: 0.3, pointRadius: 4
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#9298a8", font: { size: 10 } } } },
      scales: {
        x: { ticks: { color: "#9298a8" }, grid: { color: "rgba(45,49,64,0.5)" } },
        y: { title: { display: true, text: "温度 Temp (C)", color: "#9298a8" }, ticks: { color: "#9298a8" }, grid: { color: "rgba(45,49,64,0.5)" } }
      }
    }
  });
}

function drawSensitivityChart(data) {
  var canvas = document.getElementById("chart-sensitivity");
  if (!canvas) return;
  if (sensitivityChart) sensitivityChart.destroy();
  var sweeps = data.detailed_sweeps || data.sweeps || {};
  var datasets = [];
  var colors = ["#4a9eff", "#e74c3c", "#2ecc71", "#f1c40f", "#e67e22", "#6c5ce7"];
  var idx = 0;
  Object.entries(sweeps).forEach(function(entry) {
    var param = entry[0], sweep = entry[1];
    if (!sweep.results || !sweep.results.length) return;
    datasets.push({
      label: param,
      data: sweep.results.map(function(r) { return { x: r.parameter_value || 0, y: r.quality_score || 0 }; }),
      borderColor: colors[idx % colors.length],
      tension: 0.3, pointRadius: 3, fill: false
    });
    idx++;
  });
  if (!datasets.length) return;
  sensitivityChart = new Chart(canvas.getContext("2d"), {
    type: "line",
    data: { datasets: datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#9298a8", font: { size: 9 } } } },
      scales: {
        x: { type: "linear", title: { display: true, text: "参数值 Parameter Value", color: "#9298a8" }, ticks: { color: "#9298a8", font: { size: 9 } }, grid: { color: "rgba(45,49,64,0.5)" } },
        y: { title: { display: true, text: "质量分数 Quality Score", color: "#9298a8" }, ticks: { color: "#9298a8", font: { size: 9 } }, grid: { color: "rgba(45,49,64,0.5)" } }
      }
    }
  });
}

// Modal & Tabs
function closeReport() { document.getElementById("report-modal").classList.add("hidden"); }

function copyReport() {
  navigator.clipboard.writeText(document.getElementById("report-body").textContent)
    .then(function() { showStatus(currentLang === "zh" ? "已复制" : "Copied", "success"); });
}

function setupTabs() {
  document.getElementById("tab-nav").addEventListener("click", function(e) {
    if (!e.target.classList.contains("tab")) return;
    setActiveTab(e.target.dataset.tab);
  });
}
