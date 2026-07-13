// Data Lab - Experiment management, statistics, conclusions
// 数据实验室 - 实验管理、统计分析、研究结论

let currentProjectId = null;
let currentExperiments = [];

// ---- View Switching / 视图切换 ----
function switchView(view) {
  document.querySelectorAll('.view-btn').forEach(function(b) {
    b.classList.toggle('active', b.dataset.view === view);
  });
  document.getElementById('view-analysis').classList.toggle('hidden', view !== 'analysis');
  document.getElementById('view-datalab').classList.toggle('hidden', view !== 'datalab');
  if (view === 'datalab') {
    loadProjects();
    loadExperiments();
  }
}

// ---- Project Management / 项目管理 ----
async function loadProjects() {
  try {
    var res = await fetch(API + '/projects');
    var data = await res.json();
    var sel = document.getElementById('sel-project');
    sel.innerHTML = '<option value="">All Projects / 全部项目</option>';
    (data.projects || []).forEach(function(p) {
      var opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.name + ' (' + (p.exp_count || 0) + ')';
      sel.appendChild(opt);
    });
  } catch(e) { console.error('Failed to load projects:', e); }
}

async function createProject() {
  var name = prompt('Project name / 项目名称:');
  if (!name) return;
  try {
    await fetch(API + '/projects', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: name, description: ''})
    });
    await loadProjects();
  } catch(e) { showStatus('Failed to create project', 'error'); }
}

// ---- Experiment CRUD / 实验CRUD ----
async function loadExperiments() {
  var pid = document.getElementById('sel-project').value;
  currentProjectId = pid || null;
  var search = document.getElementById('inp-search').value;
  var grade = document.getElementById('sel-grade-filter').value;
  var params = new URLSearchParams({limit: '200', sort_by: 'created_at', sort_order: 'DESC'});
  if (pid) params.set('project_id', pid);
  if (search) params.set('search', search);
  if (grade) params.set('grade_filter', grade);
  try {
    var res = await fetch(API + '/experiments?' + params.toString());
    var data = await res.json();
    currentExperiments = data.experiments || [];
    document.getElementById('exp-count').textContent =
      'Total / 总计: ' + data.total + ' experiments / 条实验';
    renderExpList(currentExperiments);
  } catch(e) { console.error('Failed to load experiments:', e); }
}

function renderExpList(exps) {
  var container = document.getElementById('exp-list');
  if (!exps.length) {
    container.innerHTML = '<div style="color:var(--text2);padding:20px;text-align:center">No experiments yet. Add your first one! / 暂无实验数据</div>';
    return;
  }
  var h = '';
  exps.forEach(function(e) {
    var badge = e.quality_grade ? '<span class="grade-badge grade-' + e.quality_grade + '">' + e.quality_grade + '</span>' : '';
    h += '<div class="exp-card" onclick="viewExperiment(' + e.id + ')">';
    h += '<div class="exp-header"><span class="exp-name">' + (e.exp_name || 'Exp #' + e.id) + '</span>' + badge + '</div>';
    h += '<div class="exp-meta">' + (e.base_material || '') + ' | ' + (e.process || '') + ' | ' + (e.environment || '') + '</div>';
    h += '<div class="exp-meta">' + (e.exp_date || '') + ' | Score: ' + (e.quality_score !== null ? e.quality_score : 'N/A') + '</div>';
    h += '</div>';
  });
  container.innerHTML = h;
}

function showAddExperiment() {
  var h = '<div class="modal-overlay" id="exp-modal" onclick="if(event.target===this)closeExpModal()">';
  h += '<div class="modal-box"><h3>Add Experiment / 添加实验</h3>';
  h += '<div class="form-row-compact">';
  h += '<div class="form-group"><label>Name / 名称</label><input id="f-exp-name"></div>';
  h += '<div class="form-group"><label>Date / 日期</label><input id="f-exp-date" type="date" value="' + new Date().toISOString().slice(0,10) + '"></div>';
  h += '<div class="form-group"><label>Operator / 操作员</label><input id="f-operator"></div>';
  h += '<div class="form-group"><label>Material / 材料</label><select id="f-material"></select></div>';
  h += '<div class="form-group"><label>Process / 工艺</label><select id="f-process"><option value="GTAW">GTAW</option><option value="GMAW">GMAW</option><option value="SMAW">SMAW</option><option value="FCAW">FCAW</option><option value="SAW">SAW</option><option value="PAW">PAW</option><option value="LBW">LBW</option><option value="EBW">EBW</option></select></div>';
  h += '<div class="form-group"><label>Current (A) / 电流</label><input id="f-current" type="number" value="150"></div>';
  h += '<div class="form-group"><label>Voltage (V) / 电压</label><input id="f-voltage" type="number" value="20"></div>';
  h += '<div class="form-group"><label>Speed (mm/s) / 速度</label><input id="f-speed" type="number" value="2" step="0.1"></div>';
  h += '<div class="form-group"><label>Preheat (C) / 预热</label><input id="f-preheat" type="number" value="25"></div>';
  h += '<div class="form-group"><label>Thickness (mm) / 板厚</label><input id="f-thickness" type="number" value="10"></div>';
  h += '<div class="form-group"><label>Environment / 环境</label><select id="f-env"></select></div>';
  h += '</div>';
  h += '<div style="text-align:right;margin-top:12px">';
  h += '<button class="btn primary small" onclick="addExperiment()">Save / 保存</button>';
  h += '<button class="btn outline small" style="margin-left:6px" onclick="closeExpModal()">Cancel / 取消</button>';
  h += '</div></div></div>';
  var div = document.createElement('div');
  div.innerHTML = h;
  document.body.appendChild(div.firstElementChild);
  // Populate materials
  populateFormMaterials();
  // Populate environments
  populateFormEnvironments();
}

async function populateFormMaterials() {
  try {
    var res = await fetch(API + '/materials');
    var data = await res.json();
    var sel = document.getElementById('f-material');
    if (!sel) return;
    Object.entries(data.materials).forEach(function(e) {
      var opt = document.createElement('option');
      opt.value = e[0]; opt.textContent = e[1].name;
      sel.appendChild(opt);
    });
  } catch(e) {}
}

async function populateFormEnvironments() {
  try {
    var res = await fetch(API + '/environments');
    var data = await res.json();
    var sel = document.getElementById('f-env');
    if (!sel) return;
    data.environments.forEach(function(env) {
      var opt = document.createElement('option');
      opt.value = env.key; opt.textContent = env.name;
      sel.appendChild(opt);
    });
  } catch(e) {}
}

function closeExpModal() {
  var m = document.getElementById('exp-modal');
  if (m) m.remove();
}

async function addExperiment() {
  var data = {
    project_id: currentProjectId,
    exp_name: document.getElementById('f-exp-name').value || 'Unnamed',
    exp_date: document.getElementById('f-exp-date').value,
    operator: document.getElementById('f-operator').value,
    base_material: document.getElementById('f-material').value,
    process: document.getElementById('f-process').value,
    current_A: parseFloat(document.getElementById('f-current').value) || 150,
    voltage_V: parseFloat(document.getElementById('f-voltage').value) || 20,
    travel_speed_mm_s: parseFloat(document.getElementById('f-speed').value) || 2,
    preheat_temp_C: parseFloat(document.getElementById('f-preheat').value) || 25,
    plate_thickness_mm: parseFloat(document.getElementById('f-thickness').value) || 10,
    environment: document.getElementById('f-env').value,
    notes: ''
  };
  try {
    await fetch(API + '/experiments', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    closeExpModal();
    loadExperiments();
    showStatus('Experiment added / 实验已添加', 'success');
  } catch(e) {
    showStatus('Failed to add experiment: ' + e.message, 'error');
  }
}

async function viewExperiment(id) {
  try {
    var res = await fetch(API + '/experiments/' + id);
    var exp = await res.json();
    var h = '<div class="modal-overlay" id="exp-detail-modal" onclick="if(event.target===this)closeExpDetail()">';
    h += '<div class="modal-box"><h3>' + (exp.exp_name || 'Exp #' + id) + '</h3>';
    h += '<div style="font-size:12px;margin-bottom:10px">';
    h += 'Material: ' + exp.base_material + ' | Process: ' + exp.process + ' | Env: ' + exp.environment + '<br>';
    h += 'Current: ' + exp.current_A + 'A | Voltage: ' + exp.voltage_V + 'V | Speed: ' + exp.travel_speed_mm_s + ' mm/s<br>';
    if (exp.quality_grade) {
      h += 'Quality: <span class="grade-badge grade-' + exp.quality_grade + '">' + exp.quality_grade + '</span> Score: ' + exp.quality_score;
    }
    h += '</div>';
    if (exp.notes) h += '<div style="font-size:11px;color:var(--text2);margin-bottom:8px">Notes: ' + exp.notes + '</div>';
    h += '<div style="text-align:right">';
    h += '<button class="btn primary small" onclick="analyzeExperiment(' + id + ')">Run Analysis / 运行分析</button>';
    h += '<button class="btn outline small" style="margin-left:4px" onclick="deleteExperiment(' + id + ')">Delete / 删除</button>';
    h += '<button class="btn outline small" style="margin-left:4px" onclick="closeExpDetail()">Close / 关闭</button>';
    h += '</div></div></div>';
    var div = document.createElement('div');
    div.innerHTML = h;
    document.body.appendChild(div.firstElementChild);
  } catch(e) { showStatus('Failed to load: ' + e.message, 'error'); }
}

function closeExpDetail() {
  var m = document.getElementById('exp-detail-modal');
  if (m) m.remove();
}

async function deleteExperiment(id) {
  if (!confirm('Delete this experiment? / 确认删除？')) return;
  try {
    await fetch(API + '/experiments/' + id, { method: 'DELETE' });
    closeExpDetail();
    loadExperiments();
    showStatus('Deleted / 已删除', 'success');
  } catch(e) { showStatus('Failed to delete: ' + e.message, 'error'); }
}

async function analyzeExperiment(id) {
  try {
    var res = await fetch(API + '/experiments/' + id);
    var exp = await res.json();
    closeExpDetail();
    // Switch to analysis view and populate
    switchView('analysis');
    // Build analysis request from experiment
    var input = {
      base_material_key: exp.base_material || 'Q345',
      parameters: {
        process: exp.process || 'GTAW', current: exp.current_A || 150,
        voltage: exp.voltage_V || 20, travel_speed: exp.travel_speed_mm_s || 2,
        preheat_temp: exp.preheat_temp_C || 25
      },
      joint: { joint_type: exp.joint_type || 'butt', plate_thickness: exp.plate_thickness_mm || 10, position: exp.weld_position || '1G' },
      environment: exp.environment || 'indoor_standard'
    };
    showStatus('Running analysis on experiment #' + id + '...', 'loading');
    var ar = await fetch(API + '/analyze', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(input)
    });
    var data = await ar.json();
    currentResults = data;
    showResults();
    renderQualityBar(data.quality || {});
    renderAllTabs(data);
    setActiveTab('tab-summary');
    // Save results back to experiment
    var q = data.quality || {};
    var a = (data.analysis || {}).summary || {};
    await fetch(API + '/experiments/' + id, {
      method: 'PUT', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        quality_score: q.quality_score, quality_grade: q.grade,
        overall_risk: a.overall_risk, heat_input_kJ_mm: a.heat_input_kJ_per_mm,
        t8_5_s: a.t8_5_s, haz_width_mm: a.haz_width_mm,
        residual_stress_MPa: a.residual_stress_MPa,
        predicted_yield_MPa: a.predicted_yield_MPa,
        corrosion_rate_mm_yr: a.corrosion_rate_mm_per_year,
        service_life_years: a.service_life_years
      })
    });
    showStatus('Analysis complete & saved / 分析完成并已保存', 'success');
  } catch(e) { showStatus('Analysis failed: ' + e.message, 'error'); }
}

function showBatchImport() {
  var h = '<div class="modal-overlay" id="csv-modal" onclick="if(event.target===this)closeCSVModal()">';
  h += '<div class="modal-box"><h3>CSV Batch Import / CSV批量导入</h3>';
  h += '<p style="font-size:11px;color:var(--text2);margin-bottom:8px">Columns / 列: exp_name, base_material, process, current, voltage, speed, preheat, thickness, environment, quality_score</p>';
  h += '<textarea id="csv-data" rows="10" style="width:100%;font-family:var(--mono);font-size:11px;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:4px;padding:8px"></textarea>';
  h += '<div style="text-align:right;margin-top:10px">';
  h += '<button class="btn primary small" onclick="importCSV()">Import / 导入</button>';
  h += '<button class="btn outline small" style="margin-left:4px" onclick="closeCSVModal()">Cancel / 取消</button>';
  h += '</div></div></div>';
  var div = document.createElement('div');
  div.innerHTML = h;
  document.body.appendChild(div.firstElementChild);
}

function closeCSVModal() {
  var m = document.getElementById('csv-modal');
  if (m) m.remove();
}

async function importCSV() {
  var csv = document.getElementById('csv-data').value;
  if (!csv.trim()) { showStatus('Paste CSV data first / 请先粘贴CSV数据', 'error'); return; }
  showStatus('Importing CSV... / 正在导入...', 'loading');
  try {
    var res = await fetch(API + '/experiments/import-csv', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ csv_data: csv, project_id: currentProjectId })
    });
    var data = await res.json();
    closeCSVModal();
    loadExperiments();
    showStatus('Imported: ' + data.added + ' / ' + data.total + ' experiments / 已导入', 'success');
  } catch(e) { showStatus('Import failed: ' + e.message, 'error'); }
}

async function exportCSV() {
  try {
    var params = currentProjectId ? '?project_id=' + currentProjectId : '';
    var res = await fetch(API + '/experiments/export/csv' + params);
    var data = await res.json();
    if (data.csv) {
      var blob = new Blob([data.csv], {type: 'text/csv'});
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url; a.download = data.filename || 'experiments_export.csv';
      a.click(); URL.revokeObjectURL(url);
      showStatus('Exported / 已导出', 'success');
    }
  } catch(e) { showStatus('Export failed: ' + e.message, 'error'); }
}

// ---- Batch Analysis from DB / 从数据库批量分析 ----
async function runBatchFromDB() {
  if (!currentExperiments.length) { showStatus('No experiments to analyze / 无实验数据', 'error'); return; }
  showStatus('Running batch analysis on ' + currentExperiments.length + ' experiments...', 'loading');
  // Process in batches of 10 to avoid timeout
  var batch = currentExperiments.slice(0, 50);
  var completed = 0;
  for (var i = 0; i < batch.length; i++) {
    var exp = batch[i];
    try {
      var input = {
        base_material_key: exp.base_material || 'Q345',
        parameters: {
          process: exp.process || 'GTAW', current: exp.current_A || 150,
          voltage: exp.voltage_V || 20, travel_speed: exp.travel_speed_mm_s || 2,
          preheat_temp: exp.preheat_temp_C || 25
        },
        joint: { joint_type: exp.joint_type || 'butt', plate_thickness: exp.plate_thickness_mm || 10 },
        environment: exp.environment || 'indoor_standard'
      };
      var ar = await fetch(API + '/analyze', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(input)
      });
      var ad = await ar.json();
      var q = ad.quality || {};
      var a = (ad.analysis || {}).summary || {};
      await fetch(API + '/experiments/' + exp.id, {
        method: 'PUT', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          quality_score: q.quality_score, quality_grade: q.grade,
          overall_risk: a.overall_risk, heat_input_kJ_mm: a.heat_input_kJ_per_mm,
          t8_5_s: a.t8_5_s, haz_width_mm: a.haz_width_mm,
          residual_stress_MPa: a.residual_stress_MPa,
          predicted_yield_MPa: a.predicted_yield_MPa,
          corrosion_rate_mm_yr: a.corrosion_rate_mm_per_year,
          service_life_years: a.service_life_years
        })
      });
      completed++;
    } catch(e) { console.error('Batch error for exp #' + exp.id + ':', e); }
  }
  showStatus('Batch analysis done: ' + completed + '/' + batch.length + ' / 批量分析完成', 'success');
  loadExperiments();
}

// ---- Statistics / 统计分析 ----
async function showStatistics() {
  if (!currentExperiments.length) { showStatus('No experiments for statistics / 无实验数据', 'error'); return; }
  showStatus('Computing statistics... / 正在计算统计...', 'loading');
  try {
    var ids = currentExperiments.map(function(e) { return e.id; });
    // Get correlation matrix
    var corrRes = await fetch(API + '/statistics/correlation', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(ids.slice(0, 200))
    });
    var corr = await corrRes.json();
    // Show overlay with results
    var h = '<div class="modal-overlay" id="stats-modal" onclick="if(event.target===this)closeStats()">';
    h += '<div class="modal-box" style="max-width:700px"><h3>Statistical Analysis / 统计分析</h3>';
    // Correlation Matrix
    h += '<div class="stat-section"><h4>Correlation Matrix / 相关系数矩阵</h4>';
    if (corr.correlation_matrix && corr.parameters) {
      h += '<table class="corr-table"><tr><td></td>';
      corr.parameters.forEach(function(p) { h += '<td><strong>' + p.split(' / ')[0] + '</strong></td>'; });
      h += '</tr>';
      corr.correlation_matrix.forEach(function(row, i) {
        h += '<tr><td><strong>' + corr.parameters[i].split(' / ')[0] + '</strong></td>';
        row.forEach(function(val) {
          var cls = Math.abs(val) > 0.7 ? (val > 0 ? 'corr-strong-pos' : 'corr-strong-neg') : (Math.abs(val) > 0.4 ? 'corr-mod' : '');
          h += '<td class="' + cls + '">' + val.toFixed(2) + '</td>';
        });
        h += '</tr>';
      });
      h += '</table>';
    }
    // Significant correlations
    if (corr.significant_correlations && corr.significant_correlations.length) {
      h += '<div style="margin-top:8px"><strong>Key Correlations / 关键相关:</strong></div>';
      corr.significant_correlations.forEach(function(s) {
        h += '<div style="font-size:11px;margin:2px 0">' + s.param1 + ' vs ' + s.param2 + ': r=' + s.correlation + ' (' + s.direction + ')</div>';
      });
    }
    h += '</div>';
    // Trend
    h += '<div class="stat-section"><h4>Quality Trend / 质量趋势</h4>';
    try {
      var trendRes = await fetch(API + '/statistics/trend', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(ids.slice(0, 200))
      });
      var trend = await trendRes.json();
      if (trend.trend) {
        h += '<div>' + trend.trend + ' | ' + (trend.trend_cn || '') + '</div>';
        h += '<div style="font-size:11px;color:var(--text2)">Correlation with sequence: r=' + trend.correlation_with_sequence + ', Slope: ' + trend.slope_per_experiment + ' pts/exp</div>';
      }
    } catch(e) {}
    h += '</div>';
    // Outliers
    h += '<div class="stat-section"><h4>Outlier Detection / 异常检测</h4>';
    try {
      var outRes = await fetch(API + '/statistics/outliers', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(ids.slice(0, 200))
      });
      var out = await outRes.json();
      if (out.outliers && out.outliers.length) {
        h += '<div>Found ' + out.outlier_count + ' outlier(s) / 发现' + out.outlier_count + '个异常值</div>';
        out.outliers.forEach(function(o) {
          h += '<div style="font-size:11px;margin:2px 0">#' + o.id + ' ' + o.exp_name + ': score=' + o.quality_score + ' (' + o.type + ')</div>';
        });
      } else { h += '<div style="color:var(--text2)">No outliers detected / 未检测到异常值</div>'; }
    } catch(e) {}
    h += '</div>';
    h += '<div style="text-align:right"><button class="btn outline small" onclick="closeStats()">Close / 关闭</button></div>';
    h += '</div></div>';
    var div = document.createElement('div');
    div.innerHTML = h;
    document.body.appendChild(div.firstElementChild);
    showStatus('Statistics ready / 统计分析完成', 'success');
  } catch(e) { showStatus('Statistics failed: ' + e.message, 'error'); }
}

function closeStats() {
  var m = document.getElementById('stats-modal');
  if (m) m.remove();
}

// ---- Conclusions / 研究结论 ----
async function showConclusions() {
  if (!currentExperiments.length) { showStatus('No experiments for conclusions / 无实验数据', 'error'); return; }
  showStatus('Generating conclusions... / 正在生成结论...', 'loading');
  try {
    var ids = currentExperiments.map(function(e) { return e.id; });
    var res = await fetch(API + '/conclusions', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(ids.slice(0, 200))
    });
    var data = await res.json();
    var h = '<div class="modal-overlay" id="conclusions-modal" onclick="if(event.target===this)closeConclusions()">';
    h += '<div class="modal-box" style="max-width:650px"><h3>Research Conclusions / 研究结论</h3>';
    // Summary
    h += '<div class="summary-panel"><pre style="font-size:11px;color:var(--text);white-space:pre-wrap;font-family:var(--mono);margin:0">' + (data.summary || '') + '</pre></div>';
    // Key Findings
    if (data.key_findings && data.key_findings.length) {
      h += '<div class="stat-section"><h4>Key Findings / 关键发现 (' + data.key_findings.length + ')</h4>';
      data.key_findings.forEach(function(f) {
        h += '<div class="conclusion-card">';
        h += '<div class="c-domain">[' + (f.domain || '') + ']</div>';
        h += '<div class="c-finding">' + (f.finding || '') + '</div>';
        h += '<div class="c-finding-cn">' + (f.finding_cn || '') + '</div>';
        if (f.detail) h += '<div class="c-finding-cn" style="margin-top:2px">' + f.detail + '</div>';
        h += '</div>';
      });
    }
    // Recommendations
    if (data.research_recommendations && data.research_recommendations.length) {
      h += '<div class="stat-section"><h4>Research Recommendations / 研究建议 (' + data.research_recommendations.length + ')</h4>';
      data.research_recommendations.forEach(function(r) {
        h += '<div class="rec-card">' + r.recommendation + '<br><span style="font-size:11px;color:var(--text2)">' + (r.recommendation_cn || '') + '</span></div>';
      });
    }
    h += '<div style="text-align:right"><button class="btn outline small" onclick="closeConclusions()">Close / 关闭</button></div>';
    h += '</div></div>';
    var div = document.createElement('div');
    div.innerHTML = h;
    document.body.appendChild(div.firstElementChild);
    showStatus('Conclusions ready / 研究结论已生成', 'success');
  } catch(e) { showStatus('Conclusions failed: ' + e.message, 'error'); }
}

function closeConclusions() {
  var m = document.getElementById('conclusions-modal');
  if (m) m.remove();
}

// Initialize data lab on load
document.addEventListener('DOMContentLoaded', function() {
  loadProjects();
});
