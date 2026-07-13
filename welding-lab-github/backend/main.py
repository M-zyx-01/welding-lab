import os as _os
import sys as _sys
_PRJ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _PRJ)

"""
Welding Lab - FastAPI Backend Server
Multi-physics welding analysis platform.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
import json
from datetime import datetime

from .data.weld_data import (
    WeldInput, MaterialSpec, WeldParameters, WeldJoint,
    WeldProcess, JointType, WeldPosition, Environment,
)
from .data.material_db import get_material, list_materials, MATERIALS
from .models.material import carbon_equivalent, weldability_assessment, filler_compatibility
from .models.energy import energy_balance, power_density, energy_efficiency, energy_intensity_distribution, environmental_energy_impact
from .analysis.predictor import run_full_analysis, predict_weld_quality
from .analysis.report import generate_report
from .analysis.inference import cross_domain_inference
from .analysis.sensitivity import sensitivity_sweep, auto_sensitivity
from .analysis.comparison import compare_scenarios
from .analysis.storage import save_scenario, load_scenario, list_saved_scenarios, delete_scenario
from .data.experiment_db import (
    init_db, create_project, list_projects, delete_project,
    add_experiment, batch_add_experiments, import_csv, get_experiment,
    list_experiments, delete_experiment, update_experiment,
    get_statistics as db_get_statistics, export_experiments_csv,
)
from .analysis.statistics import correlation_matrix, trend_analysis, outlier_detection, parameter_distribution, compare_groups
from .analysis.conclusions import derive_conclusions

app = FastAPI(title="Welding Lab", version="1.0.0",
              description="Multi-physics welding analysis platform")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.mount("/static", StaticFiles(directory=_os.path.join(_PRJ, "frontend")), name="static")


# ---- Pydantic request models ----

class MaterialSpecIn(BaseModel):
    name: str = ""
    grade: str = ""
    composition: dict = {}
    density: float = 7850.0
    melting_point: float = 1500.0
    boiling_point: float = 2900.0
    thermal_conductivity: float = 50.0
    specific_heat: float = 500.0
    cte: float = 12.0e-6
    youngs_modulus: float = 200e9
    yield_strength: float = 250e6
    tensile_strength: float = 400e6
    poisson_ratio: float = 0.3
    electrical_resistivity: float = 1.7e-7
    magnetic_permeability: float = 1.0

    def to_spec(self) -> MaterialSpec:
        return MaterialSpec(**self.model_dump())

    class Config:
        extra = "allow"


class WeldParamsIn(BaseModel):
    process: str = "GTAW"
    current: float = 150.0
    voltage: float = 20.0
    travel_speed: float = 2.0
    arc_efficiency: float = 0.75
    wire_feed_rate: Optional[float] = None
    gas_flow_rate: Optional[float] = None
    electrode_diameter: Optional[float] = None
    torch_angle: float = 90.0
    travel_angle: float = 0.0
    stickout: float = 10.0
    arc_length: float = 3.0
    polarity: str = "DCEN"
    pulse_frequency: Optional[float] = None
    preheat_temp: float = 25.0
    interpass_temp: float = 150.0

    def to_params(self) -> WeldParameters:
        d = self.model_dump()
        d["process"] = WeldProcess(d["process"])
        return WeldParameters(**d)

    class Config:
        extra = "allow"


class WeldJointIn(BaseModel):
    joint_type: str = "butt"
    position: str = "1G"
    plate_thickness: float = 10.0
    root_gap: float = 1.0
    root_face: float = 1.5
    bevel_angle: float = 30.0
    groove_type: str = "V"
    number_of_passes: int = 3

    def to_joint(self) -> WeldJoint:
        d = self.model_dump()
        d["joint_type"] = JointType(d["joint_type"])
        d["position"] = WeldPosition(d["position"])
        return WeldJoint(**d)

    class Config:
        extra = "allow"


class AnalyzeRequest(BaseModel):
    id: str = ""
    base_material_key: str = "Q345"
    filler_material_key: Optional[str] = None
    custom_base_material: Optional[MaterialSpecIn] = None
    custom_filler_material: Optional[MaterialSpecIn] = None
    parameters: WeldParamsIn = Field(default_factory=WeldParamsIn)
    joint: WeldJointIn = Field(default_factory=WeldJointIn)
    environment: str = "indoor_standard"
    notes: str = ""


class CompareRequest(BaseModel):
    scenarios: List[AnalyzeRequest] = []


class SensitivityRequest(BaseModel):
    base_scenario: AnalyzeRequest = Field(default_factory=AnalyzeRequest)
    parameter: str = "current"
    values: List[float] = [100.0, 125.0, 150.0, 175.0, 200.0]


class BatchRequest(BaseModel):
    scenarios: List[AnalyzeRequest] = []


class BatchCSVRequest(BaseModel):
    csv_data: str = ""


class LoadRequest(BaseModel):
    filename: str = ""


# ---- Helper ----

def _build_weld_input(req: AnalyzeRequest) -> WeldInput:
    base_mat = req.custom_base_material.to_spec() if req.custom_base_material else get_material(req.base_material_key)
    filler_mat = None
    if req.filler_material_key:
        filler_mat = get_material(req.filler_material_key)
    elif req.custom_filler_material:
        filler_mat = req.custom_filler_material.to_spec()
    return WeldInput(
        id=req.id, base_material=base_mat, filler_material=filler_mat,
        parameters=req.parameters.to_params(), joint=req.joint.to_joint(),
        environment=Environment(req.environment), notes=req.notes)

# ---- API Endpoints ----

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/api/materials")
async def get_materials():
    result = {}
    for key, mat in MATERIALS.items():
        ce_val = carbon_equivalent(mat)
        result[key] = {
            "name": mat.name,
            "grade": mat.grade,
            "density": mat.density,
            "melting_point": mat.melting_point,
            "yield_strength_MPa": round(mat.yield_strength / 1e6, 1),
            "tensile_strength_MPa": round(mat.tensile_strength / 1e6, 1),
            "thermal_conductivity": mat.thermal_conductivity,
            "carbon_equivalent": ce_val.get("ce_value", 0) if isinstance(ce_val, dict) else 0,
            "composition": mat.composition,
            "category": _material_category(mat),
        }
    return {"materials": result, "count": len(result)}

def _material_category(mat: MaterialSpec) -> str:
    comp = mat.composition
    if comp.get("Ti", 0) > 50:
        return "titanium"
    if comp.get("Al", 0) > 50:
        return "aluminium"
    if comp.get("Cu", 0) > 50:
        return "copper"
    if comp.get("Ni", 0) > 30:
        return "nickel"
    if comp.get("Cr", 0) > 10:
        return "stainless_steel"
    return "carbon_steel"

@app.get("/api/environments")
async def get_environments():
    envs = [
        {"key": "indoor_standard", "name_cn": "室内标准", "name": "Indoor Standard",
         "description": "标准室内环境，温度20-25C，湿度40-60%"},
        {"key": "inland", "name_cn": "内陆", "name": "Inland",
         "description": "内陆大气环境，工业/城市大气，可能含SO2"},
        {"key": "coastal", "name_cn": "沿海", "name": "Coastal",
         "description": "沿海海洋环境，高盐雾，高湿度"},
        {"key": "underwater", "name_cn": "水下(浅海)", "name": "Underwater (Shallow)",
         "description": "浅海水下环境，海水腐蚀，生物附着"},
        {"key": "deep_sea", "name_cn": "深海", "name": "Deep Sea",
         "description": "深海高压环境，低氧，高静水压力"},
        {"key": "ultra_low_temp", "name_cn": "超低温", "name": "Ultra-Low Temp",
         "description": "超低温环境（-196C LNG至-269C液氦），韧脆转变风险"},
        {"key": "ultra_high_temp", "name_cn": "超高温", "name": "Ultra-High Temp",
         "description": "超高温环境（>500C），蠕变、氧化风险"},
        {"key": "high_humidity", "name_cn": "高湿度", "name": "High Humidity",
         "description": "高湿度环境（>85% RH），电化学腐蚀加速"},
        {"key": "corrosive_chemical", "name_cn": "腐蚀性化学", "name": "Corrosive Chemical",
         "description": "化工环境，酸/碱/盐溶液，选择性腐蚀"},
        {"key": "vacuum", "name_cn": "真空", "name": "Vacuum",
         "description": "真空环境（空间模拟），无对流散热，放气风险"},
        {"key": "nuclear", "name_cn": "核环境", "name": "Nuclear",
         "description": "核辐射环境，辐照脆化，应力腐蚀开裂"},
        {"key": "space", "name_cn": "太空", "name": "Space",
         "description": "太空轨道环境，原子氧侵蚀，热循环（-150至+150C/圈）"},
    ]
    return {"environments": envs, "count": len(envs)}

@app.post("/api/analyze")
async def api_analyze(req: AnalyzeRequest):
    weld = _build_weld_input(req)
    analysis = run_full_analysis(weld)
    quality = predict_weld_quality(weld)
    return {"analysis": analysis, "quality": quality, "id": weld.id}

@app.post("/api/quick")
async def api_quick(req: AnalyzeRequest):
    weld = _build_weld_input(req)
    quality = predict_weld_quality(weld)
    return quality

@app.get("/api/report")
async def api_report(
    base_material_key: str = "Q345",
    filler_material_key: str = None,
    process: str = "GTAW",
    current: float = 150.0,
    voltage: float = 20.0,
    travel_speed: float = 2.0,
    joint_type: str = "butt",
    plate_thickness: float = 10.0,
    environment: str = "indoor_standard",
):
    params = WeldParamsIn(process=process, current=current, voltage=voltage, travel_speed=travel_speed)
    joint_in = WeldJointIn(joint_type=joint_type, plate_thickness=plate_thickness)
    req = AnalyzeRequest(
        base_material_key=base_material_key,
        filler_material_key=filler_material_key,
        parameters=params, joint=joint_in, environment=environment)
    weld = _build_weld_input(req)
    analysis = run_full_analysis(weld)
    quality = predict_weld_quality(weld)
    report_text = generate_report(weld, analysis, quality)
    return {"report": report_text}

@app.post("/api/inference")
async def api_inference(req: AnalyzeRequest):
    weld = _build_weld_input(req)
    analysis = run_full_analysis(weld)
    return cross_domain_inference(weld, analysis)

@app.post("/api/compare")
async def api_compare(req: CompareRequest):
    if len(req.scenarios) < 2:
        raise HTTPException(status_code=400, detail="At least 2 scenarios required for comparison")
    welds = [_build_weld_input(s) for s in req.scenarios]
    return compare_scenarios(welds)

@app.post("/api/sensitivity")
async def api_sensitivity(req: SensitivityRequest):
    weld = _build_weld_input(req.base_scenario)
    return sensitivity_sweep(weld, req.parameter, req.values)

@app.post("/api/auto-sensitivity")
async def api_auto_sensitivity(req: AnalyzeRequest):
    weld = _build_weld_input(req)
    return auto_sensitivity(weld)

@app.post("/api/batch")
async def api_batch(req: BatchRequest):
    results = []
    for i, s in enumerate(req.scenarios):
        weld = _build_weld_input(s)
        analysis = run_full_analysis(weld)
        quality = predict_weld_quality(weld)
        results.append({
            "index": i, "id": s.id, "material": s.base_material_key,
            "quality": quality, "summary": analysis.get("summary", {}),
        })
    return {"count": len(results), "results": results}

@app.post("/api/batch-csv")
async def api_batch_csv(req: BatchCSVRequest):
    import io, csv
    reader = csv.DictReader(io.StringIO(req.csv_data))
    results = []
    for i, row in enumerate(reader):
        try:
            params = WeldParamsIn(
                process=row.get("process", "GTAW"),
                current=float(row.get("current", 150)),
                voltage=float(row.get("voltage", 20)),
                travel_speed=float(row.get("travel_speed", 2.0)),
                preheat_temp=float(row.get("preheat_temp", 25)),
            )
            joint_in = WeldJointIn(
                joint_type=row.get("joint_type", "butt"),
                plate_thickness=float(row.get("plate_thickness", 10)),
            )
            req_single = AnalyzeRequest(
                id=f"csv-{i}", base_material_key=row.get("base_material", "Q345"),
                environment=row.get("environment", "indoor_standard"),
                parameters=params, joint=joint_in,
            )
            weld = _build_weld_input(req_single)
            analysis = run_full_analysis(weld)
            quality = predict_weld_quality(weld)
            results.append({
                "index": i, "material": row.get("base_material", "Q345"),
                "process": row.get("process", "GTAW"),
                "quality_score": quality["quality_score"],
                "quality_grade": quality["grade"],
                "overall_risk": analysis["summary"]["overall_risk"],
            })
        except Exception as e:
            results.append({"index": i, "error": str(e)})
    return {"count": len(results), "results": results}

@app.get("/api/scenarios")
async def api_list_scenarios():
    return {"scenarios": list_saved_scenarios()}

@app.post("/api/scenarios/save")
async def api_save_scenario(req: AnalyzeRequest):
    weld = _build_weld_input(req)
    filename = save_scenario(weld)
    return {"saved": True, "filename": filename}

@app.post("/api/scenarios/load")
async def api_load_scenario(req: LoadRequest):
    try:
        weld = load_scenario(req.filename)
        return {
            "loaded": True, "id": weld.id, "material": weld.base_material.name,
            "parameters": {
                "process": weld.parameters.process.value,
                "current": weld.parameters.current,
                "voltage": weld.parameters.voltage,
                "travel_speed": weld.parameters.travel_speed,
                "preheat_temp": weld.parameters.preheat_temp,
                "polarity": weld.parameters.polarity,
            },
            "joint": {"joint_type": weld.joint.joint_type.value,
                      "plate_thickness": weld.joint.plate_thickness,
                      "position": weld.joint.position.value},
            "environment": weld.environment.value, "notes": weld.notes,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/api/scenarios/{filename}")
async def api_delete_scenario(filename: str):
    if delete_scenario(filename):
        return {"deleted": True, "filename": filename}
    raise HTTPException(status_code=404, detail=f"Scenario '{filename}' not found")


@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    return FileResponse(_os.path.join(_PRJ, "frontend", "index.html"))
# ---- New Endpoints: Experiment Management / 实验管理 ----

class ProjectCreate(BaseModel):
    name: str
    description: str = ""

class ExperimentData(BaseModel):
    project_id: Optional[int] = None
    exp_name: str = ""
    exp_date: str = ""
    operator: str = ""
    notes: str = ""
    base_material: str = "Q345"
    filler_material: str = ""
    process: str = "GTAW"
    current_A: float = 150
    voltage_V: float = 20
    travel_speed_mm_s: float = 2.0
    arc_efficiency: float = 0.75
    electrode_diameter_mm: float = 2.4
    torch_angle_deg: float = 90
    polarity: str = "DCEN"
    preheat_temp_C: float = 25
    interpass_temp_C: float = 150
    joint_type: str = "butt"
    weld_position: str = "1G"
    plate_thickness_mm: float = 10
    bevel_angle_deg: float = 30
    groove_type: str = "V"
    number_of_passes: int = 3
    environment: str = "indoor_standard"
    quality_score: Optional[float] = None
    quality_grade: str = ""
    overall_risk: str = ""
    heat_input_kJ_mm: Optional[float] = None
    t8_5_s: Optional[float] = None
    haz_width_mm: Optional[float] = None
    residual_stress_MPa: Optional[float] = None
    predicted_yield_MPa: Optional[float] = None
    corrosion_rate_mm_yr: Optional[float] = None
    service_life_years: Optional[float] = None
    analysis_json: Optional[dict] = None
    tags: str = ""

class BatchExperimentData(BaseModel):
    records: List[dict] = []

class CSVImportData(BaseModel):
    csv_data: str = ""
    project_id: Optional[int] = None

class ExperimentUpdateData(BaseModel):
    exp_name: Optional[str] = None
    notes: Optional[str] = None
    operator: Optional[str] = None
    exp_date: Optional[str] = None
    project_id: Optional[int] = None
    quality_score: Optional[float] = None
    quality_grade: Optional[str] = None
    overall_risk: Optional[str] = None
    heat_input_kJ_mm: Optional[float] = None
    t8_5_s: Optional[float] = None
    haz_width_mm: Optional[float] = None
    residual_stress_MPa: Optional[float] = None
    predicted_yield_MPa: Optional[float] = None
    corrosion_rate_mm_yr: Optional[float] = None
    service_life_years: Optional[float] = None
    analysis_json: Optional[dict] = None
    tags: Optional[str] = None

# ---- Project APIs / 项目管理 ----

@app.get("/api/projects")
async def api_list_projects():
    return {"projects": list_projects()}

@app.post("/api/projects")
async def api_create_project(req: ProjectCreate):
    return create_project(req.name, req.description)

@app.delete("/api/projects/{project_id}")
async def api_delete_project(project_id: int):
    delete_project(project_id)
    return {"deleted": True, "id": project_id}

# ---- Experiment APIs / 实验数据管理 ----

@app.get("/api/experiments")
async def api_list_experiments(
    project_id: Optional[int] = None, limit: int = 100, offset: int = 0,
    search: str = "", sort_by: str = "created_at", sort_order: str = "DESC",
    grade_filter: str = ""
):
    return list_experiments(project_id, limit, offset, search, sort_by, sort_order, grade_filter)

@app.get("/api/experiments/{exp_id}")
async def api_get_experiment(exp_id: int):
    exp = get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found / 实验未找到")
    return exp

@app.post("/api/experiments")
async def api_add_experiment(req: ExperimentData):
    data = req.model_dump(exclude_none=True)
    # Remove None for analysis_json
    if data.get("analysis_json") is None:
        del data["analysis_json"]
    result = add_experiment(data)
    return result

@app.post("/api/experiments/batch")
async def api_batch_add_experiments(req: BatchExperimentData):
    return batch_add_experiments(req.records)

@app.post("/api/experiments/import-csv")
async def api_import_csv(req: CSVImportData):
    return import_csv(req.csv_data, req.project_id)

@app.put("/api/experiments/{exp_id}")
async def api_update_experiment(exp_id: int, req: ExperimentUpdateData):
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    if update_experiment(exp_id, data):
        return {"updated": True, "id": exp_id}
    raise HTTPException(status_code=404, detail="Experiment not found / 实验未找到")

@app.delete("/api/experiments/{exp_id}")
async def api_delete_experiment(exp_id: int):
    delete_experiment(exp_id)
    return {"deleted": True, "id": exp_id}

@app.get("/api/experiments/export/csv")
async def api_export_csv(project_id: Optional[int] = None):
    csv_data = export_experiments_csv(project_id)
    if not csv_data:
        return {"error": "No data to export / 无数据可导出"}
    return {"csv": csv_data, "filename": f"experiments_export_{datetime.now().strftime('%Y%m%d')}.csv"}

# ---- Statistics APIs / 统计分析 ----

@app.get("/api/statistics")
async def api_statistics(project_id: Optional[int] = None):
    return db_get_statistics(project_id)

@app.post("/api/statistics/correlation")
async def api_correlation(experiment_ids: List[int] = []):
    exps = []
    if experiment_ids:
        for eid in experiment_ids:
            exp = get_experiment(eid)
            if exp:
                exps.append(exp)
    else:
        result = list_experiments(limit=500)
        exps = result["experiments"]
    return correlation_matrix(exps)

@app.post("/api/statistics/trend")
async def api_trend(experiment_ids: List[int] = []):
    exps = []
    if experiment_ids:
        for eid in experiment_ids:
            exp = get_experiment(eid)
            if exp:
                exps.append(exp)
    else:
        result = list_experiments(limit=500)
        exps = result["experiments"]
    return trend_analysis(exps)

@app.post("/api/statistics/outliers")
async def api_outliers(experiment_ids: List[int] = []):
    exps = []
    if experiment_ids:
        for eid in experiment_ids:
            exp = get_experiment(eid)
            if exp:
                exps.append(exp)
    else:
        result = list_experiments(limit=500)
        exps = result["experiments"]
    return outlier_detection(exps)

@app.get("/api/statistics/distribution/{parameter}")
async def api_distribution(parameter: str, project_id: Optional[int] = None):
    result = list_experiments(project_id, limit=500)
    return parameter_distribution(result["experiments"], parameter)

@app.post("/api/statistics/compare-groups")
async def api_compare_groups(group_by: str = "process", experiment_ids: List[int] = []):
    exps = []
    if experiment_ids:
        for eid in experiment_ids:
            exp = get_experiment(eid)
            if exp:
                exps.append(exp)
    else:
        result = list_experiments(limit=500)
        exps = result["experiments"]
    return compare_groups(exps, group_by)

# ---- Conclusions API / 研究结论 ----

@app.post("/api/conclusions")
async def api_conclusions(experiment_ids: List[int] = []):
    exps = []
    if experiment_ids:
        for eid in experiment_ids:
            exp = get_experiment(eid)
            if exp:
                exps.append(exp)
    else:
        result = list_experiments(limit=500)
        exps = result["experiments"]
    return derive_conclusions(exps)

# ---- Energy Analysis APIs / 能量分析 ----

class EnergyRequest(BaseModel):
    base_material_key: str = "Q345"
    parameters: WeldParamsIn = Field(default_factory=WeldParamsIn)
    joint: WeldJointIn = Field(default_factory=WeldJointIn)
    environment: str = "indoor_standard"

@app.post("/api/energy/analyze")
async def api_energy_analyze(req: EnergyRequest):
    mat = get_material(req.base_material_key)
    params = req.parameters.to_params()
    joint = req.joint.to_joint()
    env = Environment(req.environment)
    balance = energy_balance(params, mat, joint)
    pd_data = power_density(params)
    eff_data = energy_efficiency(params, mat, joint)
    intensity = energy_intensity_distribution(params, mat)
    env_impact = environmental_energy_impact(mat, env)
    return {
        "energy_balance": balance,
        "power_density": pd_data,
        "efficiency": eff_data,
        "intensity_distribution": intensity,
        "environmental_impact": env_impact,
    }

