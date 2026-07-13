"""
Report generator: structured bilingual analysis reports with energy domain.
报告生成器：包含能量域的结构化双语分析报告。
"""
from datetime import datetime
from ..data.weld_data import WeldInput
from ..models.energy import energy_balance, power_density, energy_efficiency


def generate_report(weld: WeldInput, analysis: dict = None, quality: dict = None) -> str:
    """Generate a comprehensive bilingual analysis report.
    生成完整的双语分析报告。"""
    from .predictor import run_full_analysis, predict_weld_quality
    if analysis is None:
        analysis = run_full_analysis(weld)
    if quality is None:
        quality = predict_weld_quality(weld)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    energy = energy_balance(weld.parameters, weld.base_material, weld.joint)
    pd_data = power_density(weld.parameters)
    eff_data = energy_efficiency(weld.parameters, weld.base_material, weld.joint)

    lines = []
    lines.append("=" * 65)
    lines.append("  Welding Intelligence Lab Analysis Report")
    lines.append("  焊接智能分析实验室 - 分析报告")
    lines.append("=" * 65)
    lines.append(f"  Generated / 生成时间: {now}")
    lines.append(f"  Scenario ID / 场景编号: {weld.id or 'N/A'}")
    lines.append("")

    # Quality Overview / 质量概览
    lines.append("-" * 65)
    lines.append("  1. QUALITY OVERVIEW / 质量概览")
    lines.append("-" * 65)
    qs = quality.get("quality_score", 0)
    qg = quality.get("grade", "N/A")
    qi = quality.get("interpretation", "")
    lines.append(f"  Score / 评分: {qs}/100    Grade / 等级: {qg}")
    lines.append(f"  Assessment / 评估: {qi}")
    ded = quality.get("deductions", [])
    if ded:
        lines.append("  Deduction Factors / 扣分因素:")
        for d in ded:
            lines.append(f"    - {d}")
    lines.append("")

    # Material / 材料
    m = analysis.get("material", {})
    w = m.get("weldability", {})
    lines.append("-" * 65)
    lines.append("  2. MATERIAL ANALYSIS / 材料分析")
    lines.append("-" * 65)
    lines.append(f"  Base / 母材: {m.get('base_material','N/A')} ({m.get('base_grade','')})")
    lines.append(f"  Filler / 焊材: {m.get('filler_material','Autogenous / 自熔')}")
    lines.append(f"  Carbon Equivalent (CE) / 碳当量: {m.get('carbon_equivalent','N/A')}")
    lines.append(f"  Cracking Risk / 裂纹风险: {w.get('cracking_risk','N/A')}")
    lines.append(f"  Suggested Preheat / 建议预热: {w.get('suggested_preheat_C','N/A')} C")
    lines.append(f"  Suggested Interpass / 建议层间: {w.get('suggested_interpass_max_C','N/A')} C")
    fc = m.get("filler_compatibility", {})
    if fc:
        lines.append(f"  Filler Compatibility / 焊材兼容性: {fc.get('overall','N/A')}")
        lines.append(f"    Strength Match / 强度匹配: {fc.get('strength_match','N/A')}")
        lines.append(f"    CTE Match / 热膨胀匹配: {fc.get('cte_match','N/A')}")
    lines.append("")

    # Energy / 能量
    lines.append("-" * 65)
    lines.append("  3. ENERGY ANALYSIS / 能量分析")
    lines.append("-" * 65)
    lines.append(f"  Input Power / 输入功率: {energy.get('input_power_W','N/A')} W")
    lines.append(f"  Power to Workpiece / 工件功率: {energy.get('power_to_workpiece_W','N/A')} W")
    lines.append(f"  Energy per Length / 线能量: {energy.get('energy_per_length_J_per_m','N/A')} J/m")
    lines.append(f"  Melting Efficiency / 熔化效率: {energy.get('melting_efficiency','N/A')}")
    lines.append(f"  Power Density / 功率密度: {pd_data.get('power_density_W_per_mm2','N/A')} W/mm2")
    lines.append(f"  Power Regime / 功率模式: {pd_data.get('power_regime','N/A')}")
    lines.append(f"  Energy Fluence / 能量通量: {pd_data.get('energy_fluence_J_per_mm2','N/A')} J/mm2")
    lines.append(f"  Specific Energy / 比能量: {eff_data.get('specific_energy_kJ_per_kg','N/A')} kJ/kg")
    lines.append(f"  Efficiency vs Benchmark / 效率基准比: {eff_data.get('efficiency_vs_benchmark','N/A')}")
    lines.append("")

    # Thermal / 热学
    t = analysis.get("thermal", {})
    hi = t.get("heat_input", {})
    cool = t.get("cooling", {})
    haz = t.get("haz", {})
    lines.append("-" * 65)
    lines.append("  4. THERMAL ANALYSIS / 热学分析")
    lines.append("-" * 65)
    lines.append(f"  Heat Input / 热输入: {hi.get('net_heat_input_kJ_per_mm','N/A')} kJ/mm")
    lines.append(f"  Arc Power / 电弧功率: {hi.get('arc_power_W','N/A')} W")
    lines.append(f"  t8/5 Cooling Time / 冷却时间: {cool.get('t8_5_seconds','N/A')} s")
    lines.append(f"  Cooling Regime / 冷却区: {cool.get('cooling_regime','N/A')}")
    lines.append(f"  Microstructure / 微观组织: {cool.get('microstructure_prediction','N/A')}")
    lines.append(f"  HAZ Width / 热影响区宽: {haz.get('estimated_haz_width_mm','N/A')} mm")
    lines.append(f"  Thermal Diffusion / 热扩散长: {haz.get('thermal_diffusion_length_mm','N/A')} mm")
    lines.append("")

    # Mechanical / 力学
    me = analysis.get("mechanical", {})
    rs = me.get("residual_stress", {})
    ws = me.get("weld_strength", {})
    dist = me.get("distortion", {})
    lines.append("-" * 65)
    lines.append("  5. MECHANICAL ANALYSIS / 力学分析")
    lines.append("-" * 65)
    lines.append(f"  Residual Stress / 残余应力: {rs.get('estimated_residual_stress_MPa','N/A')} MPa ({rs.get('stress_level','')})")
    lines.append(f"  Stress/Yield Ratio / 应力屈服比: {rs.get('stress_to_yield_ratio','N/A')}")
    lines.append(f"  Predicted Yield / 预测屈服: {ws.get('predicted_yield_strength_MPa','N/A')} MPa")
    lines.append(f"  Joint Efficiency / 接头效率: {ws.get('joint_efficiency','N/A')}")
    lines.append(f"  Design Strength / 设计强度: {ws.get('design_strength_MPa','N/A')} MPa (SF={ws.get('suggested_safety_factor','N/A')})")
    lines.append(f"  Buckling Risk / 屈曲风险: {dist.get('buckling_risk','N/A')}")
    lines.append(f"  Angular Distortion / 角变形: {dist.get('angular_distortion_deg','N/A')} deg")
    lines.append("")

    # Fluid / 流体
    f = analysis.get("fluid", {})
    mar = f.get("marangoni", {})
    pool = f.get("pool_geometry", {})
    lines.append("-" * 65)
    lines.append("  6. FLUID DYNAMICS / 流体动力学")
    lines.append("-" * 65)
    lines.append(f"  Marangoni Number / 马兰戈尼数: {mar.get('marangoni_number','N/A')}")
    lines.append(f"  Reynolds Number / 雷诺数: {mar.get('reynolds_number','N/A')}")
    lines.append(f"  Flow Regime / 流态: {mar.get('flow_regime','N/A')}")
    lines.append(f"  Flow Direction / 流向: {mar.get('flow_direction','N/A')}")
    lines.append(f"  Pool Width / 熔池宽: {pool.get('pool_width_mm','N/A')} mm")
    lines.append(f"  Pool Depth / 熔池深: {pool.get('pool_depth_mm','N/A')} mm")
    lines.append(f"  W/D Ratio / 宽深比: {pool.get('width_to_depth_ratio','N/A')}")
    lines.append("")

    # EM / 电磁
    em = analysis.get("electromagnetic", {})
    lor = em.get("lorentz", {})
    ab = em.get("arc_blow", {})
    ems = em.get("em_stirring", {})
    lines.append("-" * 65)
    lines.append("  7. ELECTROMAGNETIC ANALYSIS / 电磁分析")
    lines.append("-" * 65)
    lines.append(f"  Lorentz Force / 洛伦兹力: {lor.get('lorentz_force_density_N_per_m3','N/A')} N/m3")
    lines.append(f"  Arc Pressure / 电弧压力: {lor.get('arc_pressure_Pa','N/A')} Pa")
    lines.append(f"  Current Density / 电流密度: {lor.get('current_density_A_per_m2','N/A')} A/m2")
    lines.append(f"  Arc Blow Risk / 磁偏吹风险: {ab.get('arc_blow_risk_level','N/A')}")
    lines.append(f"  EM Stirring / 电磁搅拌: {ems.get('em_stirring_assessment','N/A')} (Ha={ems.get('hartmann_number','N/A')})")
    lines.append("")

    # Environmental / 环境
    env_a = analysis.get("environmental", {})
    corr = env_a.get("corrosion", {})
    sl = env_a.get("service_life", {})
    hicc = env_a.get("hydrogen_cracking", {})
    fat = env_a.get("fatigue", {})
    lines.append("-" * 65)
    lines.append("  8. ENVIRONMENTAL ASSESSMENT / 环境评估")
    lines.append("-" * 65)
    lines.append(f"  Environment / 环境: {weld.environment.value}")
    lines.append(f"  Corrosion Rate / 腐蚀速率: {corr.get('corrosion_rate_mm_per_year','N/A')} mm/yr")
    lines.append(f"  Mechanism / 机制: {corr.get('mechanism','N/A')}")
    lines.append(f"  Risk Level / 风险: {corr.get('risk_level','N/A')}")
    lines.append(f"  Est. Service Life / 预计寿命: {sl.get('estimated_service_life_years','N/A')} years")
    lines.append(f"  Fatigue Limit / 疲劳极限: {fat.get('fatigue_limit_MPa','N/A')} MPa")
    lines.append(f"  Fatigue Life / 疲劳寿命: {fat.get('estimated_life_years','N/A')} years ({fat.get('life_regime','')})")
    lines.append(f"  HICC Risk / 氢致裂纹: {hicc.get('hicc_risk','N/A')}")
    if sl.get("dbtt_note"):
        lines.append(f"  DBTT Note / 韧脆转变: {sl['dbtt_note']}")
    lines.append("")

    # Summary / 总结
    s = analysis.get("summary", {})
    lines.append("-" * 65)
    lines.append("  9. SUMMARY & RECOMMENDATIONS / 总结与建议")
    lines.append("-" * 65)
    lines.append(f"  Overall Risk / 综合风险: {s.get('overall_risk','N/A')}")
    lines.append(f"  Heat Input / 热输入: {s.get('heat_input_kJ_per_mm','N/A')} kJ/mm")
    lines.append(f"  t8/5: {s.get('t8_5_s','N/A')} s")
    lines.append(f"  HAZ Width / 热影响区: {s.get('haz_width_mm','N/A')} mm")
    lines.append(f"  Residual Stress / 残余应力: {s.get('residual_stress_MPa','N/A')} MPa")
    lines.append(f"  Predicted Yield / 预测屈服: {s.get('predicted_yield_MPa','N/A')} MPa")
    lines.append(f"  Corrosion Rate / 腐蚀速率: {s.get('corrosion_rate_mm_per_year','N/A')} mm/yr")
    lines.append(f"  Service Life / 服役寿命: {s.get('service_life_years','N/A')} years")
    lines.append("  Key Recommendations / 关键建议:")
    recs = s.get("key_recommendations", [])
    if recs:
        for r in recs:
            lines.append(f"    - {r}")
    else:
        lines.append("    (No critical recommendations / 无关键建议)")
    lines.append("")
    lines.append("=" * 65)
    lines.append("  End of Report / 报告结束")
    lines.append("=" * 65)

    return "\n".join(lines)
