"""
Scenario comparison: side-by-side multi-scenario analysis.
情景对比：多情景并列分析。
"""
from typing import Dict, List, Any
from ..data.weld_data import WeldInput
from .predictor import run_full_analysis, predict_weld_quality


def compare_scenarios(scenarios: List[WeldInput]) -> dict:
    """Run full analysis on multiple scenarios and produce comparison matrix.
    
    对多个情景运行完整分析并生成对比矩阵。
    """
    results = []
    for i, weld in enumerate(scenarios):
        analysis = run_full_analysis(weld)
        quality = predict_weld_quality(weld)
        results.append({
            "index": i,
            "id": weld.id,
            "material": weld.base_material.name,
            "filler": weld.filler_material.name if weld.filler_material else "Autogenous / 自熔",
            "process": weld.parameters.process.value,
            "environment": weld.environment.value,
            "quality_score": quality["quality_score"],
            "quality_grade": quality["grade"],
            "heat_input_kJ_per_mm": analysis["thermal"]["heat_input"]["net_heat_input_kJ_per_mm"],
            "t8_5_s": analysis["thermal"]["cooling"]["t8_5_seconds"],
            "haz_width_mm": analysis["thermal"]["haz"]["estimated_haz_width_mm"],
            "residual_stress_MPa": analysis["mechanical"]["residual_stress"]["estimated_residual_stress_MPa"],
            "predicted_yield_MPa": analysis["mechanical"]["weld_strength"]["predicted_yield_strength_MPa"],
            "corrosion_rate_mm_per_yr": analysis["environmental"]["corrosion"]["corrosion_rate_mm_per_year"],
            "service_life_years": analysis["environmental"]["service_life"]["estimated_service_life_years"],
            "hicc_risk": analysis["environmental"]["hydrogen_cracking"]["hicc_risk"],
            "arc_blow_risk": analysis["electromagnetic"]["arc_blow"]["arc_blow_risk_level"],
            "overall_risk": analysis["summary"]["overall_risk"],
            "key_deductions": quality["deductions"],
        })
    
    # Comparison analysis
    if len(results) < 2:
        return {"scenarios": results, "comparison": None}
    
    best = max(results, key=lambda r: r["quality_score"])
    worst = min(results, key=lambda r: r["quality_score"])
    
    comparison = {
        "best_scenario": {"index": best["index"], "id": best["id"], "score": best["quality_score"]},
        "worst_scenario": {"index": worst["index"], "id": worst["id"], "score": worst["quality_score"]},
        "score_spread": best["quality_score"] - worst["quality_score"],
        "ranking": sorted(results, key=lambda r: r["quality_score"], reverse=True),
        "trade_off_analysis": _trade_offs(results),
    }
    
    return {"scenarios": results, "comparison": comparison}


def _trade_offs(results: List[dict]) -> List[dict]:
    """Identify trade-offs: e.g., best quality vs. highest service life may differ."""
    if len(results) < 2:
        return []
    
    best_quality = max(results, key=lambda r: r["quality_score"])
    best_life = max(results, key=lambda r: r["service_life_years"])
    lowest_stress = min(results, key=lambda r: r["residual_stress_MPa"])
    
    trades = []
    
    if best_quality["index"] != best_life["index"]:
        trades.append({
            "type": "Quality vs Service Life / 质量 vs 服役寿命",
            "finding": f"Best quality: Scenario {best_quality['index']} (Score {best_quality['quality_score']}); "
                       f"Best service life: Scenario {best_life['index']} ({best_life['service_life_years']:.1f} yr)",
            "finding_cn": f"最佳质量：情景{best_quality['index']}（分数{best_quality['quality_score']}）；"
                          f"最佳服役寿命：情景{best_life['index']}（{best_life['service_life_years']:.1f}年）",
            "implication": "Process optimization needed: balance heat input for quality vs. material selection for environment.",
            "implication_cn": "需要工艺优化：在质量热输入与环境的材料选择之间取得平衡。",
        })
    
    if best_quality["index"] != lowest_stress["index"]:
        trades.append({
            "type": "Quality vs Residual Stress / 质量 vs 残余应力",
            "finding": f"Best quality has residual stress {best_quality['residual_stress_MPa']:.0f} MPa; "
                       f"Lowest stress scenario has {lowest_stress['residual_stress_MPa']:.0f} MPa but lower quality.",
            "finding_cn": f"最佳质量残余应力{best_quality['residual_stress_MPa']:.0f} MPa；"
                          f"最低应力情景{lowest_stress['residual_stress_MPa']:.0f} MPa但质量较低。",
            "implication": "Consider PWHT for the best-quality scenario to relieve residual stress.",
            "implication_cn": "考虑对最佳质量情景进行焊后热处理以消除残余应力。",
        })
    
    return trades
