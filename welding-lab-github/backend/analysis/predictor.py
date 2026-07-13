"""Prediction engine: synthesises all analysis modules and produces predictions."""
from ..data.weld_data import WeldInput, WeldParameters, WeldJoint, MaterialSpec, Environment
from ..models.material import carbon_equivalent, weldability_assessment, filler_compatibility
from ..models.thermal import heat_input, cooling_rate_t800_t500, haz_width_estimate, peak_temperature_distribution
from ..models.mechanical import residual_stress_estimate, weld_strength_prediction, distortion_analysis
from ..models.fluid import marangoni_number, weld_pool_geometry, buoyancy_effect
from ..models.electromagnetic import lorentz_force, magnetic_arc_blow_risk, electromagnetic_stirring
from ..models.environmental import corrosion_rate_estimate, service_life_estimate, hydrogen_cracking_risk, fatigue_life_estimate
from ..models.energy import energy_balance, power_density, energy_efficiency, energy_intensity_distribution, environmental_energy_impact

def run_full_analysis(weld: WeldInput) -> dict:
    """Run the complete multi-physics analysis pipeline on a weld scenario."""
    mat = weld.base_material
    filler = weld.filler_material if weld.filler_material else mat
    params = weld.parameters
    joint = weld.joint
    env = weld.environment

    results = {"id": weld.id, "timestamp": "", "summary": {}}

    # --- Material ---
    results["material"] = {
        "base_material": mat.name,
        "base_grade": mat.grade,
        "filler_material": filler.name if weld.filler_material else "Autogenous",
        "carbon_equivalent": carbon_equivalent(mat),
        "weldability": weldability_assessment(mat),
    }
    if weld.filler_material:
        results["material"]["filler_compatibility"] = filler_compatibility(mat, filler)

    # --- Thermal ---
    hi = heat_input(params)
    results["thermal"] = {
        "heat_input": hi,
        "cooling": cooling_rate_t800_t500(params, mat, joint.plate_thickness),
        "haz": haz_width_estimate(params, mat),
        "peak_temperatures": peak_temperature_distribution(params, mat, joint.plate_thickness),
    }

    # --- Mechanical ---
    results["mechanical"] = {
        "residual_stress": residual_stress_estimate(mat, params, joint),
        "weld_strength": weld_strength_prediction(mat, filler, joint),
        "distortion": distortion_analysis(params, mat, joint),
    }

    # --- Fluid ---
    results["fluid"] = {
        "marangoni": marangoni_number(params, mat),
        "pool_geometry": weld_pool_geometry(params, mat),
        "buoyancy": buoyancy_effect(params, mat),
    }

    # --- Electromagnetic ---
    results["electromagnetic"] = {
        "lorentz": lorentz_force(params),
        "arc_blow": magnetic_arc_blow_risk(params, joint, mat),
        "em_stirring": electromagnetic_stirring(params, mat),
    }

    # --- Environmental ---
    results["environmental"] = {
        "corrosion": corrosion_rate_estimate(mat, env),
        "service_life": service_life_estimate(mat, env, joint),
        "hydrogen_cracking": hydrogen_cracking_risk(mat, params, env),
        "fatigue": fatigue_life_estimate(mat, env),
    }

    # --- Energy ---
    results["energy"] = {
        "balance": energy_balance(params, mat, joint),
        "power_density": power_density(params),
        "efficiency": energy_efficiency(params, mat, joint),
        "intensity_distribution": energy_intensity_distribution(params, mat),
        "environmental_impact": environmental_energy_impact(mat, env),
    }

    # --- Summary ---
    risks = []
    if results["material"]["weldability"]["cracking_risk"] in ("High", "Very High"):
        risks.append("Cold cracking risk: " + results["material"]["weldability"]["cracking_risk"])
    corr = results["environmental"]["corrosion"]
    if corr["risk_level"] in ("High", "Very High"):
        risks.append("Corrosion risk: " + corr["risk_level"])
    hicc = results["environmental"]["hydrogen_cracking"]
    if hicc["hicc_risk"] in ("Severe", "High"):
        risks.append("HICC/HAC risk: " + hicc["hicc_risk"])
    ab = results["electromagnetic"]["arc_blow"]
    if ab["arc_blow_risk_level"] == "Severe":
        risks.append("Arc blow risk: Severe")
    rs = results["mechanical"]["residual_stress"]
    if rs["stress_level"].startswith("Exceeds"):
        risks.append("Residual stress exceeds yield: distortion/cracking expected")

    all_risk = len([r for r in risks if "Severe" in r or "Very High" in r or "Exceeds" in r])
    if all_risk >= 3: overall_risk = "Critical"
    elif all_risk >= 1: overall_risk = "High"
    elif len(risks) > 2: overall_risk = "Moderate"
    elif len(risks) > 0: overall_risk = "Low"
    else: overall_risk = "Acceptable"

    results["summary"] = {
        "risks": risks,
        "overall_risk": overall_risk,
        "heat_input_kJ_per_mm": hi["net_heat_input_kJ_per_mm"],
        "t8_5_s": results["thermal"]["cooling"]["t8_5_seconds"],
        "haz_width_mm": results["thermal"]["haz"]["estimated_haz_width_mm"],
        "residual_stress_MPa": results["mechanical"]["residual_stress"]["estimated_residual_stress_MPa"],
        "predicted_yield_MPa": results["mechanical"]["weld_strength"]["predicted_yield_strength_MPa"],
        "corrosion_rate_mm_per_year": corr["corrosion_rate_mm_per_year"],
        "service_life_years": results["environmental"]["service_life"]["estimated_service_life_years"],
        "key_recommendations": _collect_recommendations(results),
    }

    return results

def _collect_recommendations(results: dict) -> list:
    recs = []
    w = results["material"].get("weldability", {})
    recs.extend(w.get("recommendations", []))
    fc = results["material"].get("filler_compatibility", {})
    recs.extend(fc.get("notes", []))
    ab = results["electromagnetic"]["arc_blow"]
    recs.extend(ab.get("mitigations", []))
    hicc = results["environmental"]["hydrogen_cracking"]
    recs.extend(hicc.get("mitigations", []))
    return list(dict.fromkeys(recs))  # deduplicate

def predict_weld_quality(weld: WeldInput) -> dict:
    """Quick quality prediction for screening purposes."""
    analysis = run_full_analysis(weld)
    score = 100
    deductions = []
    ce = analysis["material"]["carbon_equivalent"]
    if ce > 0.60: score -= 20; deductions.append(f"High CE ({ce:.3f})")
    elif ce > 0.45: score -= 10; deductions.append(f"Moderate CE ({ce:.3f})")
    t85 = analysis["thermal"]["cooling"]["t8_5_seconds"]
    if t85 < 3: score -= 15; deductions.append("???? (?????)")
    elif t85 < 10: score -= 5
    rs = analysis["mechanical"]["residual_stress"]
    if rs["stress_to_yield_ratio"] > 0.9: score -= 15; deductions.append("????????")
    elif rs["stress_to_yield_ratio"] > 0.7: score -= 8
    ab = analysis["electromagnetic"]["arc_blow"]
    if ab["arc_blow_risk_level"] == "Severe": score -= 15; deductions.append("???????")
    elif ab["arc_blow_risk_level"] == "Moderate": score -= 5
    hicc = analysis["environmental"]["hydrogen_cracking"]
    if hicc["hicc_risk"] == "Severe": score -= 20; deductions.append("????????")
    elif hicc["hicc_risk"] == "High": score -= 10
    corr = analysis["environmental"]["corrosion"]
    if corr["risk_level"] == "Very High": score -= 15; deductions.append("??????")
    elif corr["risk_level"] == "High": score -= 8
    if score < 0: score = 0
    if score >= 85: grade = "A"; interpretation = "??????????????????"
    elif score >= 70: grade = "B"; interpretation = "?????????"
    elif score >= 55: grade = "C"; interpretation = "?????????"
    elif score >= 40: grade = "D"; interpretation = "???????????????????"
    else: grade = "F"; interpretation = "????????????"
    return {"quality_score": score, "grade": grade, "interpretation": interpretation, "deductions": deductions}
