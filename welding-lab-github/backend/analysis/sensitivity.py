"""
Sensitivity analysis: parameter sweep to identify dominant factors.
敏感性分析：参数扫描以识别主导因素。
"""
import copy, math
from typing import Dict, List, Any
from ..data.weld_data import WeldInput, WeldParameters, MaterialSpec, WeldJoint, Environment
from ..data.material_db import get_material
from .predictor import run_full_analysis, predict_weld_quality


def sensitivity_sweep(weld: WeldInput,
                      parameter: str,
                      values: List[float]) -> dict:
    """Sweep a single parameter and track how key outputs respond.
    
    扫描单个参数并跟踪关键输出如何响应。
    """
    results = []
    base_quality = predict_weld_quality(weld)["quality_score"]
    
    for val in values:
        variant = _apply_variant(weld, parameter, val)
        analysis = run_full_analysis(variant)
        quality = predict_weld_quality(variant)
        
        outputs = {
            "parameter_value": val,
            "quality_score": quality["quality_score"],
            "quality_grade": quality["grade"],
            "heat_input_kJ_per_mm": analysis["thermal"]["heat_input"]["net_heat_input_kJ_per_mm"],
            "t8_5_s": analysis["thermal"]["cooling"]["t8_5_seconds"],
            "haz_width_mm": analysis["thermal"]["haz"]["estimated_haz_width_mm"],
            "residual_stress_MPa": analysis["mechanical"]["residual_stress"]["estimated_residual_stress_MPa"],
            "predicted_yield_MPa": analysis["mechanical"]["weld_strength"]["predicted_yield_strength_MPa"],
            "corrosion_rate_mm_per_yr": analysis["environmental"]["corrosion"]["corrosion_rate_mm_per_year"],
            "service_life_years": analysis["environmental"]["service_life"]["estimated_service_life_years"],
            "arc_blow_risk": analysis["electromagnetic"]["arc_blow"]["arc_blow_risk_level"],
        }
        results.append(outputs)
    
    # Identify which outputs are most sensitive to this parameter
    impact = _calc_impact(results, base_quality)
    
    return {
        "parameter": parameter,
        "base_value": _get_param_value(weld.parameters, parameter),
        "base_quality_score": base_quality,
        "sweep_results": results,
        "impact_analysis": impact,
    }


def _apply_variant(weld: WeldInput, parameter: str, value: float) -> WeldInput:
    """Create a variant with one parameter changed."""
    variant = copy.deepcopy(weld)
    params = variant.parameters
    
    param_map = {
        "current": "current",
        "voltage": "voltage",
        "travel_speed": "travel_speed",
        "arc_efficiency": "arc_efficiency",
        "preheat_temp": "preheat_temp",
        "interpass_temp": "interpass_temp",
        "arc_length": "arc_length",
        "torch_angle": "torch_angle",
        "travel_angle": "travel_angle",
        "stickout": "stickout",
        "electrode_diameter": "electrode_diameter",
        "plate_thickness": "plate_thickness",
        "bevel_angle": "bevel_angle",
        "number_of_passes": "number_of_passes",
    }
    
    if param_map.get(parameter) in vars(params):
        setattr(params, param_map[parameter], value)
    elif parameter in ("plate_thickness", "bevel_angle", "number_of_passes"):
        setattr(variant.joint, parameter, value)
    
    return variant


def _get_param_value(params: WeldParameters, parameter: str) -> float:
    """Get current value of a parameter."""
    param_map = {
        "current": params.current,
        "voltage": params.voltage,
        "travel_speed": params.travel_speed,
        "arc_efficiency": params.arc_efficiency,
        "preheat_temp": params.preheat_temp,
        "interpass_temp": params.interpass_temp,
        "arc_length": params.arc_length,
        "torch_angle": params.torch_angle,
        "travel_angle": params.travel_angle,
        "stickout": params.stickout,
        "electrode_diameter": params.electrode_diameter or 0,
    }
    return param_map.get(parameter, 0)


def _calc_impact(results: List[dict], base_quality: float) -> dict:
    """Calculate which outputs change the most when parameter varies."""
    if len(results) < 2:
        return {"description": "Insufficient data for impact analysis"}
    
    quality_range = max(r["quality_score"] for r in results) - min(r["quality_score"] for r in results)
    heat_range = max(r["heat_input_kJ_per_mm"] for r in results) - min(r["heat_input_kJ_per_mm"] for r in results)
    stress_range = max(r["residual_stress_MPa"] for r in results) - min(r["residual_stress_MPa"] for r in results)
    
    impacts = []
    if quality_range > 10:
        impacts.append(("Quality Score / 质量分数", f"Varies by ±{quality_range/2:.0f} pts", "High / 高"))
    elif quality_range > 3:
        impacts.append(("Quality Score / 质量分数", f"Varies by ±{quality_range/2:.0f} pts", "Moderate / 中"))
    else:
        impacts.append(("Quality Score / 质量分数", "Minimal change / 变化极小", "Low / 低"))
    
    if heat_range > 0.5:
        impacts.append(("Heat Input / 热输入", f"Range: {heat_range:.3f} kJ/mm", "High / 高"))
    elif heat_range > 0.1:
        impacts.append(("Heat Input / 热输入", f"Range: {heat_range:.3f} kJ/mm", "Moderate / 中"))
    
    if stress_range > 50:
        impacts.append(("Residual Stress / 残余应力", f"Range: {stress_range:.0f} MPa", "High / 高"))
    
    return {
        "quality_variation": quality_range,
        "dominant_effects": impacts,
        "sensitivity_summary": f"This parameter causes {quality_range:.1f}-point quality score variation",
    }


def auto_sensitivity(weld: WeldInput) -> dict:
    """Run automated sensitivity on top-6 parameters to find critical ones.
    
    对前6个关键参数进行自动敏感性分析，找出关键参数。
    """
    params_to_test = [
        ("current", [weld.parameters.current * f for f in [0.7, 0.85, 1.0, 1.15, 1.3]]),
        ("voltage", [weld.parameters.voltage * f for f in [0.8, 0.9, 1.0, 1.1, 1.2]]),
        ("travel_speed", [weld.parameters.travel_speed * f for f in [0.5, 0.75, 1.0, 1.5, 2.0]]),
        ("preheat_temp", [max(0, weld.parameters.preheat_temp + d) for d in [-50, -25, 0, 50, 100]]),
        ("arc_efficiency", [max(0.3, min(1.0, weld.parameters.arc_efficiency * f)) for f in [0.7, 0.85, 1.0, 1.15, 1.3]]),
        ("plate_thickness", [max(2, weld.joint.plate_thickness * f) for f in [0.5, 0.75, 1.0, 1.5, 2.0]]),
    ]
    
    all_sweeps = {}
    for param_name, values in params_to_test:
        sweep = sensitivity_sweep(weld, param_name, [round(v, 1) for v in values])
        all_sweeps[param_name] = {
            "quality_range": sweep["impact_analysis"]["quality_variation"],
            "results": sweep["sweep_results"],
        }
    
    # Rank parameters by impact
    ranked = sorted(all_sweeps.items(), key=lambda x: x[1]["quality_range"], reverse=True)
    
    return {
        "critical_parameters": [
            {"parameter": name, "quality_impact_range": data["quality_range"],
             "interpretation": "Dominant / 主导" if data["quality_range"] > 10 else ("Significant / 显著" if data["quality_range"] > 3 else "Minor / 次要")}
            for name, data in ranked
        ],
        "detailed_sweeps": all_sweeps,
    }
