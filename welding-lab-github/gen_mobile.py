import os, json

PRJ = r"E:\焊接\welding-lab"

# ============================================================
# Create a fully offline HTML demo page with embedded data
# This can be shared as a single file, opened directly on any phone
# ============================================================

html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#4a9eff">
<title>焊接智能分析实验室</title>
<style>
:root{--bg:#0f1117;--surface:#1a1d27;--surface2:#222530;--border:#2d3140;--text:#e1e4ed;--text2:#9298a8;--accent:#4a9eff;--accent2:#6c5ce7;--green:#2ecc71;--yellow:#f1c40f;--orange:#e67e22;--red:#e74c3c;--radius:6px;--font:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:var(--font);font-size:14px;line-height:1.5;padding:16px;padding-bottom:env(safe-area-inset-bottom,16px)}
h1{font-size:22px;color:var(--accent);text-align:center;margin-bottom:4px}
.subtitle{text-align:center;color:var(--text2);font-size:13px;margin-bottom:20px}
.card{background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:14px;margin-bottom:12px}
.card h2{font-size:15px;font-weight:600;color:var(--text2);margin-bottom:10px;text-transform:uppercase;letter-spacing:1px}
.form-group{margin-bottom:10px}
.form-group label{display:block;font-size:12px;color:var(--text2);margin-bottom:4px}
.form-row{display:flex;gap:10px;flex-wrap:wrap}
.form-row .form-group{flex:1;min-width:45%}
select,input{padding:10px 12px;background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);color:var(--text);font-size:15px;font-family:var(--font);width:100%;-webkit-appearance:none;appearance:none;min-height:44px}
select{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M6 8L1 3h10z' fill='%239298a8'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center;padding-right:32px}
input:focus,select:focus{outline:none;border-color:var(--accent)}
.btn{padding:12px 16px;border-radius:var(--radius);font-size:14px;font-weight:600;cursor:pointer;border:1px solid transparent;transition:all .15s;font-family:var(--font);text-align:center;width:100%;min-height:44px}
.btn.primary{background:var(--accent);color:#fff;margin-bottom:8px}
.btn.secondary{background:var(--accent2);color:#fff}
.result-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:12px;margin-bottom:8px}
.result-card .label{font-size:10px;text-transform:uppercase;color:var(--text2)}
.result-card .value{font-size:16px;font-weight:600;color:var(--text);margin-top:4px}
.risk-low{color:var(--green)}.risk-moderate{color:var(--yellow)}.risk-high{color:var(--orange)}.risk-severe{color:var(--red)}
.quality-bar{display:flex;align-items:center;gap:12px;padding:14px;border-radius:var(--radius);margin-bottom:14px;font-weight:600}
.grade-A{background:rgba(46,204,113,.15);border:1px solid rgba(46,204,113,.3)}.grade-B{background:rgba(46,204,113,.1)}
.grade-C{background:rgba(241,196,15,.15);border:1px solid rgba(241,196,15,.3)}.grade-D{background:rgba(230,126,34,.15)}
.grade-F{background:rgba(231,76,60,.15);border:rgba(231,76,60,.3)}
.grade-circle{font-size:28px;font-weight:800;width:52px;height:52px;display:flex;align-items:center;justify-content:center;border-radius:50%}
.grade-A .grade-circle{background:var(--green);color:#000}.grade-B .grade-circle{background:var(--green);color:#000;opacity:.8}
.grade-C .grade-circle{background:var(--yellow);color:#000}.grade-D .grade-circle{background:var(--orange);color:#fff}.grade-F .grade-circle{background:var(--red);color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}
.info-row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border);font-size:13px}
.info-row .key{color:var(--text2)}.info-row .val{font-weight:600}
.section{margin-bottom:16px}.section h3{font-size:14px;color:var(--accent);margin-bottom:8px;border-left:3px solid var(--accent);padding-left:8px}
li{padding:6px 8px;margin-bottom:4px;font-size:13px;background:var(--surface);border-left:3px solid var(--green);border-radius:0 var(--radius) var(--radius) 0}
#results{display:none}#results.show{display:block}
</style>
</head>
<body>

<h1>焊接智能分析实验室</h1>
<div class="subtitle">Welding Intelligence Lab</div>

<div class="card">
  <h2>母材 Base Material</h2>
  <div class="form-group">
    <select id="baseMat"></select>
  </div>
</div>

<div class="card">
  <h2>焊材 Filler Metal</h2>
  <div class="form-group">
    <select id="fillerMat"><option value="">自熔 Autogenous</option></select>
  </div>
</div>

<div class="card">
  <h2>焊接参数 Weld Parameters</h2>
  <div class="form-row">
    <div class="form-group"><label>工艺 Process</label><select id="process"></select></div>
    <div class="form-group"><label>极性 Polarity</label><select id="polarity"><option>DCEN</option><option>DCEP</option><option>AC</option></select></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label>电流 Current (A)</label><input type="number" id="current" value="150" min="10" max="1000"></div>
    <div class="form-group"><label>电压 Voltage (V)</label><input type="number" id="voltage" value="20" min="5" max="80"></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label>速度 Speed (mm/s)</label><input type="number" id="speed" value="2" min="0.1" max="50"></div>
    <div class="form-group"><label>板厚 Thickness (mm)</label><input type="number" id="thickness" value="10" min="1" max="200"></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label>预热 Preheat (C)</label><input type="number" id="preheat" value="25" min="0" max="600"></div>
    <div class="form-group"><label>层间 Interpass (C)</label><input type="number" id="interpass" value="150" min="25" max="600"></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label>接头 Joint</label><select id="jointType"><option value="butt">对接 Butt</option><option value="lap">搭接 Lap</option><option value="tee">T型 Tee</option><option value="corner">角接 Corner</option></select></div>
    <div class="form-group"><label>位置 Position</label><select id="position"><option value="1G">1G 平焊</option><option value="2G">2G 横焊</option><option value="3G">3G 立焊</option><option value="4G">4G 仰焊</option></select></div>
  </div>
</div>

<div class="card">
  <h2>服役环境 Environment</h2>
  <div class="form-group">
    <select id="environment">
      <option value="indoor_standard">室内标准 Indoor</option>
      <option value="inland">内陆 Inland</option>
      <option value="coastal">沿海 Coastal</option>
      <option value="underwater">水下 Underwater</option>
      <option value="deep_sea">深海 Deep Sea</option>
      <option value="ultra_low_temp">超低温 Ultra-Low Temp</option>
      <option value="ultra_high_temp">超高温 Ultra-High Temp</option>
      <option value="high_humidity">高湿度 High Humidity</option>
      <option value="corrosive_chemical">腐蚀性化学 Corrosive</option>
      <option value="vacuum">真空 Vacuum</option>
      <option value="nuclear">核环境 Nuclear</option>
      <option value="space">太空 Space</option>
    </select>
  </div>
</div>

<button class="btn primary" onclick="runAnalysis()">开始分析 Analyze</button>

<div id="results">
  <div id="qualityBar"></div>

  <div class="section"><h3>总览 Summary</h3><div id="summary" class="grid"></div></div>
  <div class="section"><h3>热学 Thermal</h3><div id="thermal" class="grid"></div></div>
  <div class="section"><h3>力学 Mechanical</h3><div id="mechanical" class="grid"></div></div>
  <div class="section"><h3>环境 Environmental</h3><div id="env" class="grid"></div></div>
  <div class="section"><h3>建议 Recommendations</h3><ul id="recs"></ul></div>
</div>

<script>
// ===== Material Database (Embedded) =====
const MATERIALS = {
  "A36":{name:"ASTM A36 Carbon Steel",yield:250,tensile:400,density:7860,mp:1460,tc:52,cte:11.7,comp:{C:0.25,Mn:0.8,Fe:98.66}},
  "Q345":{name:"Q345 (16Mn) Low-Alloy Steel",yield:345,tensile:490,density:7850,mp:1480,tc:48,cte:12.0,comp:{C:0.18,Mn:1.4,Fe:97.94}},
  "Q235":{name:"Q235 Carbon Steel",yield:235,tensile:375,density:7850,mp:1470,tc:50,cte:12.0,comp:{C:0.17,Mn:0.5,Fe:98.99}},
  "Q460":{name:"Q460 High-Strength Steel",yield:460,tensile:550,density:7850,mp:1470,tc:45,cte:12.0,comp:{C:0.15,Mn:1.6,Fe:97.73}},
  "Q690":{name:"Q690 Q&T Steel",yield:690,tensile:770,density:7850,mp:1460,tc:40,cte:12.0,comp:{C:0.16,Mn:1.5,Cr:0.5,Fe:96.74}},
  "S355":{name:"S355 Structural Steel",yield:355,tensile:490,density:7850,mp:1470,tc:49,cte:12.0,comp:{C:0.2,Mn:1.5,Fe:97.74}},
  "304":{name:"AISI 304 Stainless Steel",yield:205,tensile:515,density:8000,mp:1425,tc:16.2,cte:17.3,comp:{C:0.07,Cr:18.5,Ni:8.5,Fe:70.87}},
  "316L":{name:"AISI 316L Stainless Steel",yield:290,tensile:558,density:8000,mp:1400,tc:15,cte:16.0,comp:{C:0.02,Cr:17,Ni:12,Mo:2.5,Fe:66.43}},
  "2205":{name:"2205 Duplex SS",yield:450,tensile:620,density:7800,mp:1430,tc:19,cte:13.0,comp:{Cr:22,Ni:5.5,Mo:3,Fe:67.81}},
  "Inconel 625":{name:"Inconel 625",yield:517,tensile:930,density:8440,mp:1330,tc:9.8,cte:12.8,comp:{Ni:62,Cr:21.5,Mo:9,Fe:3}},
  "Inconel 718":{name:"Inconel 718",yield:1034,tensile:1275,density:8190,mp:1300,tc:11.4,cte:13.0,comp:{Ni:53,Cr:19,Fe:18,Nb:5.1}},
  "Monel 400":{name:"Monel 400 (Ni-Cu)",yield:240,tensile:550,density:8800,mp:1340,tc:21.8,cte:13.9,comp:{Ni:65,Cu:32,Fe:1.5}},
  "6061-T6":{name:"AA 6061-T6 Aluminium",yield:276,tensile:310,density:2700,mp:585,tc:167,cte:23.6,comp:{Al:97.9,Mg:1,Si:0.6}},
  "5083":{name:"AA 5083 Aluminium Marine",yield:228,tensile:317,density:2660,mp:590,tc:120,cte:24.7,comp:{Al:94.4,Mg:4.5}},
  "7075-T6":{name:"AA 7075-T6 Aluminium",yield:503,tensile:572,density:2810,mp:535,tc:130,cte:23.4,comp:{Al:90,Zn:5.5,Mg:2.5,Cu:1.6}},
  "Ti-6Al-4V":{name:"Ti-6Al-4V Grade 5",yield:880,tensile:950,density:4430,mp:1660,tc:6.7,cte:8.6,comp:{Ti:89.9,Al:6,V:4}},
  "C11000":{name:"C11000 ETP Copper",yield:70,tensile:220,density:8940,mp:1083,tc:388,cte:17.0,comp:{Cu:99.9}},
  "ER70S-6":{name:"ER70S-6 GMAW Wire",yield:420,tensile:500,density:7850,mp:1470,tc:50,cte:12.0,comp:{C:0.08,Mn:1.5,Si:0.9,Fe:97.52}},
  "ER308L":{name:"ER308L GTAW Wire (304)",yield:350,tensile:550,density:8000,mp:1440,tc:16,cte:17.3,comp:{C:0.02,Cr:20,Ni:10,Fe:67.68}},
  "ER316L":{name:"ER316L GTAW Wire (316L)",yield:370,tensile:560,density:8000,mp:1410,tc:15,cte:16.0,comp:{C:0.02,Cr:19,Ni:12.5,Mo:2.5}},
  "ER2209":{name:"ER2209 GTAW Wire (Duplex)",yield:550,tensile:700,density:7800,mp:1440,tc:18,cte:13.2,comp:{Cr:23,Ni:8.5,Mo:3.1}},
  "ERNiCrMo-3":{name:"ERNiCrMo-3 Wire (625)",yield:450,tensile:760,density:8440,mp:1330,tc:9.8,cte:12.8,comp:{Ni:64,Cr:21.5,Mo:9}},
  "ER5356":{name:"ER5356 GTAW Wire (Al-Mg)",yield:130,tensile:265,density:2660,mp:605,tc:120,cte:24.5,comp:{Al:94.4,Mg:5}},
  "E7018":{name:"E7018 SMAW Electrode",yield:420,tensile:500,density:7850,mp:1480,tc:48,cte:12.0,comp:{C:0.05,Mn:1.2,Fe:98.25}},
  "E309L":{name:"E309L SMAW Electrode",yield:400,tensile:560,density:7900,mp:1420,tc:16,cte:17.0,comp:{Cr:23,Ni:13}},
};

// Populate dropdowns
function init() {
  var b = document.getElementById('baseMat');
  var f = document.getElementById('fillerMat');
  Object.entries(MATERIALS).forEach(function(e) {
    var o = document.createElement('option');
    o.value = e[0];
    o.textContent = e[1].name + ' - ' + e[1].yield + ' MPa';
    b.appendChild(o);
    f.appendChild(o.cloneNode(true));
  });
  
  // Process dropdown
  ['GTAW','GMAW','SMAW','FCAW','SAW','PAW','LBW','EBW'].forEach(function(p) {
    var o = document.createElement('option');
    o.value = p; o.textContent = p;
    document.getElementById('process').appendChild(o);
  });
}
init();

// ===== Physics Engine =====
function analyze(mat, params, env) {
  // Heat input
  var Q = params.arcEff * params.voltage * params.current / (params.speed * 1000); // kJ/mm
  var peakTemp = 25 + (Q * 1000) / (mat.tc * params.thickness * 0.001);
  
  // HAZ width (approximate)
  var hazWidth = 0.8 * Math.sqrt((mat.tc * (mat.mp - 25)) / (mat.density * 500 * Q * 1000));
  
  // Cooling rate
  var coolingRate = 2 * Math.PI * mat.tc * Math.pow(peakTemp - 25, 2) / (Q * 1000);
  
  // Residual stress (simplified)
  var restraint = params.thickness > 20 ? 1.3 : 1.0;
  var residualStress = 0.65 * mat.yield * restraint / 1e6;
  
  // Carbon equivalent
  var c = mat.comp.C || 0, mn = mat.comp.Mn || 0, cr = mat.comp.Cr || 0;
  var mo = mat.comp.Mo || 0, v = mat.comp.V || 0, ni = mat.comp.Ni || 0, cu = mat.comp.Cu || 0;
  var ce = c + mn/6 + (cr + mo + v)/5 + (ni + cu)/15;
  
  // Hydrogen cracking risk
  var hiccScore = 0;
  if (ce > 0.5) hiccScore += 4; else if (ce > 0.35) hiccScore += 2;
  if (Q < 0.5) hiccScore += 3; else if (Q < 1.5) hiccScore += 1;
  if (['underwater','coastal','deep_sea','high_humidity','corrosive_chemical'].includes(env)) hiccScore += 3;
  var hiccRisk = hiccScore >= 7 ? 'Severe' : hiccScore >= 4 ? 'High' : hiccScore >= 2 ? 'Moderate' : 'Low';
  
  // Corrosion rate (mm/year)
  var isSS = cr > 10, hasMo = mo > 1.0, isTi = (mat.comp.Ti || 0) > 50, isAl = mat.density < 5000;
  var corrRate = 0.005;
  if (env == 'coastal') corrRate = isSS && hasMo ? 0.01 : isSS ? 0.05 : isAl ? 0.02 : isTi ? 0.001 : 0.15;
  else if (env == 'underwater') corrRate = isSS && hasMo ? 0.02 : isAl ? 0.03 : isTi ? 0.0005 : 0.30;
  else if (env == 'deep_sea') corrRate = isSS && hasMo ? 0.03 : isTi ? 0.001 : isAl ? 0.08 : 0.45;
  else if (env == 'ultra_low_temp') corrRate = 0.001;
  else if (env == 'ultra_high_temp') corrRate = isSS ? 0.05 : isTi ? 0.02 : 0.20;
  else if (env == 'corrosive_chemical') corrRate = isSS && hasMo ? 0.03 : 0.50;
  else if (env == 'space') corrRate = isTi ? 0.0001 : isSS ? 0.001 : 0.01;
  else if (env == 'nuclear') corrRate = isSS ? 0.005 : 0.05;
  else if (env == 'inland') corrRate = isSS ? 0.005 : isAl ? 0.001 : isTi ? 0.0003 : 0.04;
  
  // Service life
  var serviceLife = 2.0 / (corrRate || 0.001);
  if (serviceLife > 100) serviceLife = 100;
  
  // Fatigue limit
  var flBase = mat.tensile > 800 ? 0.45 : mat.tensile > 400 ? 0.40 : 0.35;
  flBase *= mat.tensile; // in MPa
  var derating = 1.0;
  if (env == 'coastal') derating = 0.70; else if (env == 'underwater') derating = 0.65;
  else if (env == 'deep_sea') derating = 0.55; else if (env == 'corrosive_chemical') derating = 0.50;
  else if (env == 'ultra_high_temp') derating = 0.55; else if (env == 'ultra_low_temp') derating = 1.05;
  else if (env == 'inland') derating = 0.90; else if (env == 'space') derating = 0.80;
  else if (env == 'high_humidity') derating = 0.85; else if (env == 'vacuum') derating = 0.95;
  else if (env == 'nuclear') derating = 0.75;
  var fatigueLimit = flBase * derating;
  
  // Quality score
  var score = 100;
  if (ce > 0.5) score -= 15; else if (ce > 0.35) score -= 8;
  if (Q < 0.3) score -= 12; else if (Q > 3.0) score -= 10;
  if (coolingRate > 200) score -= 10;
  if (corrRate > 0.1) score -= 15; else if (corrRate > 0.05) score -= 8;
  if (residualStress > mat.yield * 0.8 / 1e6) score -= 12;
  if (params.preheat < 50 && ce > 0.4) score -= 10;
  score = Math.max(0, Math.min(100, Math.round(score)));
  
  var grade = score >= 85 ? 'A' : score >= 70 ? 'B' : score >= 55 ? 'C' : score >= 40 ? 'D' : 'F';
  var overallRisk = score >= 85 ? 'Low' : score >= 70 ? 'Moderate' : score >= 55 ? 'Elevated' : score >= 40 ? 'High' : 'Critical';
  
  // Recommendations
  var recs = [];
  if (ce > 0.45) recs.push('碳当量偏高(CE=' + ce.toFixed(2) + ')，建议预热至 ' + Math.max(params.preheat, 150) + 'C');
  if (hiccRisk == 'Severe' || hiccRisk == 'High') recs.push('氢致裂纹风险' + hiccRisk + '：使用低氢焊材(H4/H8)，焊后250C x 2h消氢处理');
  if (corrRate > 0.05) recs.push('腐蚀速率较高(' + corrRate.toFixed(3) + ' mm/年)，建议选用耐腐蚀材料或增加腐蚀裕量');
  if (residualStress > mat.yield * 0.7 / 1e6) recs.push('残余应力偏高(' + Math.round(residualStress) + ' MPa)，建议焊后热处理(PWHT)');
  if (coolingRate > 150) recs.push('冷却速度过快(' + Math.round(coolingRate) + ' °C/s)，提高热输入或预热温度');
  if (env == 'ultra_low_temp') recs.push('超低温环境：校核DBTT，铁素体钢需冲击试验验证');
  if (env == 'ultra_high_temp') recs.push('超高温环境：校核蠕变寿命，考虑使用P91/Inconel等耐热合金');
  if (env == 'space') recs.push('太空环境：关注真空放气、原子氧侵蚀及热循环疲劳(-150/+150C)');
  if (env == 'deep_sea') recs.push('深海环境：高静水压力加速腐蚀疲劳耦合，校核HISC');
  if (mat.name.includes('Al') && (env == 'coastal' || env == 'underwater')) recs.push('铝合金海洋环境：注意电偶腐蚀防护，避免与铜/钢直接接触');
  
  if (recs.length == 0) recs.push('当前参数匹配良好，焊接质量预期合格');
  
  return {
    quality: {score: score, grade: grade, risk: overallRisk},
    thermal: {heatInput: Q.toFixed(3), peakTemp: Math.round(peakTemp), hazWidth: hazWidth.toFixed(2),
              coolingRate: Math.round(coolingRate), preheat: params.preheat + '°C'},
    mechanical: {residualStress: Math.round(residualStress), yieldStrength: mat.yield,
                 tensileStrength: mat.tensile, carbonEq: ce.toFixed(3)},
    environment: {corrRate: corrRate.toFixed(4), serviceLife: Math.round(serviceLife),
                  fatigueLimit: Math.round(fatigueLimit), hiccRisk: hiccRisk},
    recs: recs
  };
}

// ===== Run Analysis =====
function runAnalysis() {
  var matKey = document.getElementById('baseMat').value;
  if (!matKey) { alert('请选择母材 Select base material'); return; }
  
  var mat = MATERIALS[matKey];
  var fillerKey = document.getElementById('fillerMat').value;
  var filler = fillerKey ? MATERIALS[fillerKey] : null;
  
  // Use filler properties if selected, otherwise base
  var effMat = filler || mat;
  
  var params = {
    process: document.getElementById('process').value,
    current: parseFloat(document.getElementById('current').value) || 150,
    voltage: parseFloat(document.getElementById('voltage').value) || 20,
    speed: parseFloat(document.getElementById('speed').value) || 2,
    arcEff: 0.75,
    thickness: parseFloat(document.getElementById('thickness').value) || 10,
    preheat: parseFloat(document.getElementById('preheat').value) || 25,
    interpass: parseFloat(document.getElementById('interpass').value) || 150,
    jointType: document.getElementById('jointType').value,
    position: document.getElementById('position').value
  };
  var env = document.getElementById('environment').value;
  
  var result = analyze(effMat, params, env);
  
  // Render
  document.getElementById('results').classList.add('show');
  
  var q = result.quality;
  document.getElementById('qualityBar').className = 'quality-bar grade-' + q.grade;
  document.getElementById('qualityBar').innerHTML = 
    '<span class="grade-circle">' + q.grade + '</span>' +
    '<div><div style="font-size:16px">质量分数 Quality: ' + q.score + '/100</div>' +
    '<div style="font-size:12px;color:var(--text2)">风险 Risk: ' + q.risk + '</div></div>';
  
  document.getElementById('summary').innerHTML = 
    rc('材料 Material', mat.name) + rc('工艺 Process', params.process) +
    rc('接头 Joint', params.jointType + ' / ' + params.position) +
    rc('环境 Env', env.replace(/_/g, ' ')) + rc('质量 Grade', q.grade) +
    rc('风险 Risk', q.risk);
  
  document.getElementById('thermal').innerHTML = toGrid(result.thermal, {heatInput:'kJ/mm',peakTemp:'°C',hazWidth:'mm',coolingRate:'°C/s'});
  document.getElementById('mechanical').innerHTML = toGrid(result.mechanical, {residualStress:'MPa',yieldStrength:'MPa',tensileStrength:'MPa'});
  document.getElementById('env').innerHTML = toGrid(result.environment, {corrRate:'mm/yr',serviceLife:'years',fatigueLimit:'MPa',hiccRisk:''});
  
  var ul = document.getElementById('recs');
  ul.innerHTML = '';
  result.recs.forEach(function(r) {
    var li = document.createElement('li');
    li.textContent = r;
    ul.appendChild(li);
  });
  
  window.scrollTo({top: document.getElementById('results').offsetTop - 20, behavior: 'smooth'});
}

function rc(label, val) { return '<div class="result-card"><div class="label">' + label + '</div><div class="value">' + val + '</div></div>'; }

function toGrid(obj, units) {
  var h = '';
  Object.entries(obj).forEach(function(e) {
    var u = units[e[0]] ? ' ' + units[e[0]] : '';
    h += '<div class="result-card"><div class="label">' + e[0].replace(/([A-Z])/g,' $1').trim() + '</div><div class="value">' + e[1] + u + '</div></div>';
  });
  return h;
}
</script>

</body>
</html>"""

with open(os.path.join(PRJ, "WeldingLab_Mobile.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

# Also copy to outputs
import shutil
shutil.copy(os.path.join(PRJ, "WeldingLab_Mobile.html"), os.path.join(PRJ, "outputs", "WeldingLab_Mobile.html"))

print("WeldingLab_Mobile.html created - single file, works offline, share via WeChat/email")
print(f"Size: {len(html_content):,} bytes")
print(f"Location: {os.path.join(PRJ, 'WeldingLab_Mobile.html')}")
