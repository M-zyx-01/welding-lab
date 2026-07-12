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

from .data.weld_data import (
    WeldInput, MaterialSpec, WeldParameters, WeldJoint,
    WeldProcess, JointType, WeldPosition, Environment,
)
from .data.material_db import get_material, list_materials, MATERIALS
from .models.material import carbon_equivalent, weldability_assessment, filler_compatibility
from .analysis.predictor import run_full_analysis, predict_weld_quality
from .analysis.report import generate_report
from .analysis.inference import cross_domain_inference
from .analysis.sensitivity import sensitivity_sweep, auto_sensitivity
from .analysis.comparison import compare_scenarios
from .analysis.storage import save_scenario, load_scenario, list_saved_scenarios, delete_scenario

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
    return cross_domain_inference(weld)

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
