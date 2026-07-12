"""
Data persistence: save and load welding scenarios to/from local JSON files.
数据持久化：将焊接情景保存/加载到本地JSON文件。
"""
import json, os, glob
from datetime import datetime
from typing import Dict, List, Optional
from ..data.weld_data import (
    WeldInput, MaterialSpec, WeldParameters, WeldJoint,
    WeldProcess, JointType, WeldPosition, Environment,
)

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "outputs")


def _ensure_storage_dir():
    os.makedirs(STORAGE_DIR, exist_ok=True)


def save_scenario(weld: WeldInput, filename: Optional[str] = None) -> str:
    """Save a single weld scenario to JSON file.
    
    Returns the filename (without path) that was saved.
    """
    _ensure_storage_dir()
    
    if filename is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        mat = weld.base_material.name.replace(" ", "_")[:20]
        filename = f"scenario_{mat}_{ts}.json"
    
    if not filename.endswith(".json"):
        filename += ".json"
    
    data = {
        "saved_at": datetime.now().isoformat(),
        "id": weld.id,
        "notes": weld.notes,
        "base_material": {
            "name": weld.base_material.name,
            "grade": weld.base_material.grade,
            "composition": weld.base_material.composition,
            "density": weld.base_material.density,
            "melting_point": weld.base_material.melting_point,
            "thermal_conductivity": weld.base_material.thermal_conductivity,
            "specific_heat": weld.base_material.specific_heat,
            "cte": weld.base_material.cte,
            "youngs_modulus": weld.base_material.youngs_modulus,
            "yield_strength": weld.base_material.yield_strength,
            "tensile_strength": weld.base_material.tensile_strength,
            "poisson_ratio": weld.base_material.poisson_ratio,
            "electrical_resistivity": weld.base_material.electrical_resistivity,
            "magnetic_permeability": weld.base_material.magnetic_permeability,
        },
        "filler_material": None,
        "parameters": {
            "process": weld.parameters.process.value,
            "current": weld.parameters.current,
            "voltage": weld.parameters.voltage,
            "travel_speed": weld.parameters.travel_speed,
            "arc_efficiency": weld.parameters.arc_efficiency,
            "electrode_diameter": weld.parameters.electrode_diameter,
            "torch_angle": weld.parameters.torch_angle,
            "travel_angle": weld.parameters.travel_angle,
            "arc_length": weld.parameters.arc_length,
            "polarity": weld.parameters.polarity,
            "preheat_temp": weld.parameters.preheat_temp,
            "interpass_temp": weld.parameters.interpass_temp,
            "stickout": weld.parameters.stickout,
        },
        "joint": {
            "joint_type": weld.joint.joint_type.value,
            "position": weld.joint.position.value,
            "plate_thickness": weld.joint.plate_thickness,
            "root_gap": weld.joint.root_gap,
            "bevel_angle": weld.joint.bevel_angle,
            "groove_type": weld.joint.groove_type,
            "number_of_passes": weld.joint.number_of_passes,
        },
        "environment": weld.environment.value,
    }
    
    if weld.filler_material:
        data["filler_material"] = {
            "name": weld.filler_material.name,
            "grade": weld.filler_material.grade,
            "composition": weld.filler_material.composition,
            "density": weld.filler_material.density,
            "melting_point": weld.filler_material.melting_point,
            "thermal_conductivity": weld.filler_material.thermal_conductivity,
            "specific_heat": weld.filler_material.specific_heat,
            "cte": weld.filler_material.cte,
            "youngs_modulus": weld.filler_material.youngs_modulus,
            "yield_strength": weld.filler_material.yield_strength,
            "tensile_strength": weld.filler_material.tensile_strength,
            "poisson_ratio": weld.filler_material.poisson_ratio,
            "electrical_resistivity": weld.filler_material.electrical_resistivity,
            "magnetic_permeability": weld.filler_material.magnetic_permeability,
        }
    
    filepath = os.path.join(STORAGE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filename


def load_scenario(filename: str) -> WeldInput:
    """Load a weld scenario from a JSON file."""
    filepath = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(filepath):
        filepath = filename  # Try absolute path
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Reconstruct MaterialSpec
    bm = data["base_material"]
    base_mat = MaterialSpec(
        name=bm.get("name", ""), grade=bm.get("grade", ""),
        composition=bm.get("composition", {}),
        density=bm.get("density", 7850), melting_point=bm.get("melting_point", 1500),
        boiling_point=bm.get("boiling_point", 2900),
        thermal_conductivity=bm.get("thermal_conductivity", 50),
        specific_heat=bm.get("specific_heat", 500), cte=bm.get("cte", 12e-6),
        youngs_modulus=bm.get("youngs_modulus", 200e9),
        yield_strength=bm.get("yield_strength", 250e6),
        tensile_strength=bm.get("tensile_strength", 400e6),
        poisson_ratio=bm.get("poisson_ratio", 0.3),
        electrical_resistivity=bm.get("electrical_resistivity", 1.7e-7),
        magnetic_permeability=bm.get("magnetic_permeability", 1.0),
    )
    
    filler_mat = None
    if data.get("filler_material"):
        fm = data["filler_material"]
        filler_mat = MaterialSpec(
            name=fm.get("name", ""), grade=fm.get("grade", ""),
            composition=fm.get("composition", {}),
            density=fm.get("density", 7850), melting_point=fm.get("melting_point", 1500),
            boiling_point=fm.get("boiling_point", 2900),
            thermal_conductivity=fm.get("thermal_conductivity", 50),
            specific_heat=fm.get("specific_heat", 500), cte=fm.get("cte", 12e-6),
            youngs_modulus=fm.get("youngs_modulus", 200e9),
            yield_strength=fm.get("yield_strength", 250e6),
            tensile_strength=fm.get("tensile_strength", 400e6),
            poisson_ratio=fm.get("poisson_ratio", 0.3),
            electrical_resistivity=fm.get("electrical_resistivity", 1.7e-7),
            magnetic_permeability=fm.get("magnetic_permeability", 1.0),
        )
    
    # Reconstruct WeldParameters
    p = data["parameters"]
    params = WeldParameters(
        process=WeldProcess(p.get("process", "GTAW")),
        current=p.get("current", 150), voltage=p.get("voltage", 20),
        travel_speed=p.get("travel_speed", 2.0),
        arc_efficiency=p.get("arc_efficiency", 0.75),
        electrode_diameter=p.get("electrode_diameter"),
        torch_angle=p.get("torch_angle", 90), travel_angle=p.get("travel_angle", 0),
        arc_length=p.get("arc_length", 3), polarity=p.get("polarity", "DCEN"),
        preheat_temp=p.get("preheat_temp", 25),
        interpass_temp=p.get("interpass_temp", 150),
        stickout=p.get("stickout", 10),
    )
    
    # Reconstruct WeldJoint
    j = data["joint"]
    joint = WeldJoint(
        joint_type=JointType(j.get("joint_type", "butt")),
        position=WeldPosition(j.get("position", "1G")),
        plate_thickness=j.get("plate_thickness", 10),
        root_gap=j.get("root_gap", 1.0),
        bevel_angle=j.get("bevel_angle", 30.0),
        groove_type=j.get("groove_type", "V"),
        number_of_passes=j.get("number_of_passes", 3),
    )
    
    return WeldInput(
        id=data.get("id", ""),
        base_material=base_mat,
        filler_material=filler_mat,
        parameters=params,
        joint=joint,
        environment=Environment(data.get("environment", "indoor_standard")),
        notes=data.get("notes", ""),
    )


def list_saved_scenarios() -> List[dict]:
    """List all saved scenarios with metadata."""
    _ensure_storage_dir()
    scenarios = []
    for fpath in glob.glob(os.path.join(STORAGE_DIR, "scenario_*.json")):
        fname = os.path.basename(fpath)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            scenarios.append({
                "filename": fname,
                "saved_at": data.get("saved_at", ""),
                "id": data.get("id", ""),
                "material": data.get("base_material", {}).get("name", ""),
                "process": data.get("parameters", {}).get("process", ""),
                "environment": data.get("environment", ""),
            })
        except Exception:
            scenarios.append({"filename": fname, "error": "Failed to parse", "saved_at": "", "id": "", "material": "", "process": "", "environment": ""})
    return sorted(scenarios, key=lambda s: s.get("saved_at", ""), reverse=True)


def delete_scenario(filename: str) -> bool:
    """Delete a saved scenario file."""
    filepath = os.path.join(STORAGE_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False
