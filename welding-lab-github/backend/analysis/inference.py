"""
Cross-domain inference engine: connects physics domains to produce
multi-physics insights and predictive reasoning.

交叉域推理引擎：连接各物理领域，产生多物理场洞察和预测性推理。
"""
import math
from typing import Dict, List, Any
from ..data.weld_data import WeldInput, Environment


def cross_domain_inference(weld: WeldInput, analysis: dict) -> dict:
    """Synthesize cross-domain inferences from the full analysis.
    
    Produces structured insights that connect phenomena across:
    thermal ↔ mechanical, fluid ↔ EM, material ↔ environmental, etc.
    
    从完整分析中综合跨域推理。
    生成连接热-机械、流体-电磁、材料-环境等现象的结构化洞察。
    """
    inferences: List[Dict[str, str]] = []
    predictions: List[Dict[str, str]] = []
    params = weld.parameters
    mat = weld.base_material
    env = weld.environment
    
    t = analysis.get("thermal", {})
    m = analysis.get("mechanical", {})
    f = analysis.get("fluid", {})
    em = analysis.get("electromagnetic", {})
    env_a = analysis.get("environmental", {})
    mat_a = analysis.get("material", {})
    
    # 1. Thermal → Mechanical coupling
    _thermal_mechanical(t, m, mat, inferences, predictions)
    
    # 2. Fluid → Thermal → Mechanical coupling
    _fluid_thermal_mechanical(f, t, m, inferences, predictions)
    
    # 3. EM → Fluid coupling (Lorentz force stirring)
    _em_fluid(em, f, inferences, predictions)
    
    # 4. EM → Thermal (arc physics)
    _em_thermal(em, t, params, inferences, predictions)
    
    # 5. Material ↔ Environment long-term prognosis
    _material_env(mat_a, env_a, env, mat, inferences, predictions)
    
    # 6. Process → Quality holistic reasoning
    _process_quality_chain(analysis, inferences, predictions)
    
    # 7. Weld angle / position effects
    _position_effects(weld, f, m, inferences, predictions)
    
    return {
        "inferences": inferences,
        "predictions": predictions,
        "inference_count": len(inferences),
        "prediction_count": len(predictions),
    }


def _thermal_mechanical(t, m, mat, inferences, predictions):
    """Thermal → Mechanical: cooling rate → residual stress & microstructure."""
    cooling = t.get("cooling", {})
    rs = m.get("residual_stress", {})
    t85 = cooling.get("t8_5_seconds", 0)
    haz = t.get("haz", {})
    
    if t85 < 3:
        inferences.append({
            "domain": "Thermal→Mechanical / 热→力",
            "finding": "Ultra-fast cooling (t8/5 < 3 s) produces hard martensite. Expect high residual stress and potential cold cracking.",
            "finding_cn": "超快冷却（t8/5 < 3 s）产生硬马氏体。预计高残余应力和潜在的冷裂纹。",
            "confidence": "High",
        })
        predictions.append({
            "domain": "Microstructure / 微观组织",
            "prediction": "Martensite volume fraction > 80% in HAZ near fusion line. Hardness zone: 350-450 HV.",
            "prediction_cn": "热影响区靠近熔合线处马氏体体积分数 > 80%。硬度区：350-450 HV。",
            "recommendation": "Increase preheat to slow cooling rate. Consider PWHT.",
            "recommendation_cn": "提高预热温度以减缓冷却速率。考虑焊后热处理。",
        })
    elif t85 < 10:
        inferences.append({
            "domain": "Thermal→Mechanical / 热→力",
            "finding": "Moderate cooling (3 < t8/5 < 10 s): bainite + martensite mix. Intermediate strength and toughness.",
            "finding_cn": "中等冷却（3 < t8/5 < 10 s）：贝氏体+马氏体混合组织。中等强度和韧性。",
            "confidence": "Moderate",
        })
    
    str_ratio = rs.get("stress_to_yield_ratio", 0)
    if str_ratio > 0.8:
        inferences.append({
            "domain": "Thermal→Mechanical / 热→力",
            "finding": f"Residual stress at {str_ratio*100:.0f}% of yield. Thermal strain during cooling is the primary driver.",
            "finding_cn": f"残余应力达到屈服强度的{str_ratio*100:.0f}%。冷却过程中的热应变是主要驱动力。",
            "confidence": "High",
        })


def _fluid_thermal_mechanical(f, t, m, inferences, predictions):
    """Fluid dynamics affects thermal distribution → affects mechanical outcome."""
    mar = f.get("marangoni", {})
    pool = f.get("pool_geometry", {})
    direction = mar.get("flow_direction", "")
    
    if "inward" in direction.lower() or "内向" in direction:
        inferences.append({
            "domain": "Fluid→Thermal / 流体→热",
            "finding": "Inward Marangoni flow drives heat deep into the pool, producing narrow/deep penetration. This concentrates thermal stress at the root.",
            "finding_cn": "内向马兰戈尼流将热量驱入熔池深处，产生窄而深的熔透。这使热应力集中在根部。",
            "confidence": "Moderate",
        })
        predictions.append({
            "domain": "Fluid→Mechanical / 流体→力",
            "prediction": "Deep narrow pool → higher root stress concentration → increased root cracking risk in restrained joints.",
            "prediction_cn": "深窄熔池 → 根部应力集中更高 → 约束接头中根部裂纹风险增加。",
            "recommendation": "Consider Weaving or wider arc to broaden pool. Adjust sulfur content if possible.",
            "recommendation_cn": "考虑摆动焊接或加宽电弧以扩大熔池。如可能调整硫含量。",
        })
    else:
        inferences.append({
            "domain": "Fluid→Thermal / 流体→热",
            "finding": "Outward Marangoni flow produces wide/shallow pool, distributing heat more evenly across the joint face.",
            "finding_cn": "外向马兰戈尼流产生宽而浅的熔池，使热量更均匀地分布在接头表面。",
            "confidence": "Moderate",
        })
    
    wdr = pool.get("width_to_depth_ratio", 0)
    if wdr < 1.5:
        inferences.append({
            "domain": "Fluid→Mechanical / 流体→力",
            "finding": f"Low W/D ratio ({wdr:.1f}) indicates keyhole or deep penetration mode. Potential for centerline solidification cracking.",
            "finding_cn": f"低宽深比 ({wdr:.1f}) 表明匙孔或深熔模式。可能存在中心线凝固裂纹风险。",
            "confidence": "High",
        })


def _em_fluid(em, f, inferences, predictions):
    """EM forces drive fluid flow: Lorentz → Marangoni interaction."""
    lorentz = em.get("lorentz", {})
    stirring = em.get("em_stirring", {})
    ha = stirring.get("hartmann_number", 0)
    
    if ha > 10:
        inferences.append({
            "domain": "EM→Fluid / 电磁→流体",
            "finding": f"Strong EM stirring (Ha={ha:.1f}) dominates over Marangoni convection. Lorentz forces reshape the weld pool flow pattern significantly.",
            "finding_cn": f"强电磁搅拌（Ha={ha:.1f}）主导马兰戈尼对流。洛伦兹力显著重塑熔池流动模式。",
            "confidence": "High",
        })
        predictions.append({
            "domain": "EM→Fluid→Microstructure / 电磁→流体→组织",
            "prediction": "Lorentz-driven stirring homogenizes temperature and composition, reducing segregation but may increase grain size in center.",
            "prediction_cn": "洛伦兹驱动搅拌均匀化温度和成分，减少偏析但可能增加中心晶粒尺寸。",
            "recommendation": "Monitor arc stability. Consider external magnetic field control for grain refinement.",
            "recommendation_cn": "监测电弧稳定性。考虑外加磁场控制以细化晶粒。",
        })
    elif ha > 1:
        inferences.append({
            "domain": "EM→Fluid / 电磁→流体",
            "finding": f"Moderate EM stirring (Ha={ha:.1f}) assists Marangoni flow. Some grain refinement expected.",
            "finding_cn": f"中等电磁搅拌（Ha={ha:.1f}）辅助马兰戈尼流。预期有一定晶粒细化。",
            "confidence": "Moderate",
        })


def _em_thermal(em, t, params, inferences, predictions):
    """Arc physics (EM) determines heat distribution (Thermal)."""
    lorentz = em.get("lorentz", {})
    arc_p = lorentz.get("arc_pressure_Pa", 0)
    hi = t.get("heat_input", {})
    
    if arc_p > 5000:
        inferences.append({
            "domain": "EM→Thermal / 电磁→热",
            "finding": f"High arc pressure ({arc_p:.0f} Pa) depresses the pool surface, increasing effective arc length and modifying heat distribution.",
            "finding_cn": f"高电弧压力（{arc_p:.0f} Pa）压低熔池表面，增加有效弧长并改变热量分布。",
            "confidence": "Moderate",
        })
    
    if params.current > 250:
        inferences.append({
            "domain": "EM→Thermal / 电磁→热",
            "finding": "High current (> 250 A) generates strong self-magnetic field. Arc constriction increases current density and local heating.",
            "finding_cn": "高电流（> 250 A）产生强自磁场。电弧收缩增加电流密度和局部加热。",
            "confidence": "High",
        })


def _material_env(mat_a, env_a, env, mat, inferences, predictions):
    """Material-environment synergy: long-term service prognosis."""
    welda = mat_a.get("weldability", {})
    ce = mat_a.get("carbon_equivalent", 0)
    corr = env_a.get("corrosion", {})
    fat = env_a.get("fatigue", {})
    sl = env_a.get("service_life", {})
    
    is_cryogenic = env in (Environment.ULTRA_LOW_TEMP, Environment.SPACE)
    is_high_temp = env in (Environment.ULTRA_HIGH_TEMP, Environment.NUCLEAR)
    
    if is_cryogenic and ce > 0.35:
        inferences.append({
            "domain": "Material↔Environment / 材料↔环境",
            "finding": f"Cryogenic service with CE > 0.35: DBTT shift near weld increases brittle fracture risk. Charpy impact values may drop below 27 J at service temperature.",
            "finding_cn": f"低温服役且CE > 0.35：焊缝附近韧脆转变温度偏移增加脆性断裂风险。夏比冲击值可能在服役温度下降至27 J以下。",
            "confidence": "High",
        })
        predictions.append({
            "domain": "Life Prediction / 寿命预测",
            "prediction": "Risk of catastrophic brittle failure on first cold start. Recommend fracture mechanics assessment (CTOD).",
            "prediction_cn": "首次冷启动时存在灾难性脆性破坏风险。建议进行断裂力学评估（CTOD）。",
            "recommendation": "Use austenitic filler (e.g., 309L) for cryogenic toughness. PWHT at 600 C.",
            "recommendation_cn": "使用奥氏体焊材（如309L）以获得低温韧性。600 C焊后热处理。",
        })
    
    if is_high_temp and mat.composition.get("Cr", 0) < 5:
        inferences.append({
            "domain": "Material↔Environment / 材料↔环境",
            "finding": "Carbon/low-alloy steel at high temperature: expect creep cavitation at grain boundaries. Oxidation scaling accelerates above 500 C.",
            "finding_cn": "碳钢/低合金钢在高温下：预期晶界处出现蠕变空洞。500 C以上氧化剥落加速。",
            "confidence": "High",
        })
    
    cr = corr.get("corrosion_rate_mm_per_year", 0)
    sl_yrs = sl.get("estimated_service_life_years", 0)
    if sl_yrs < 10:
        predictions.append({
            "domain": "Service Life / 服役寿命",
            "prediction": f"Estimated service life < 10 years ({sl_yrs:.1f} yr) at corrosion rate {cr:.4f} mm/yr. Consider coating, cladding, or material upgrade.",
            "prediction_cn": f"预估服役寿命 < 10年（{sl_yrs:.1f}年），腐蚀速率{cr:.4f} mm/年。考虑涂层、堆焊或材料升级。",
            "recommendation": "Evaluate corrosion-resistant overlay (CRA) or cathodic protection.",
            "recommendation_cn": "评估耐腐蚀堆焊层或阴极保护。",
        })


def _process_quality_chain(analysis, inferences, predictions):
    """Holistic process-to-quality reasoning chain."""
    s = analysis.get("summary", {})
    risks = s.get("risks", [])
    risk_level = s.get("overall_risk", "Unknown")
    
    if risk_level == "Critical":
        inferences.append({
            "domain": "Process→Quality / 工艺→质量",
            "finding": "Multiple critical risks detected: " + "; ".join(risks[:3]) + ". Process parameters require fundamental redesign.",
            "finding_cn": "检测到多个关键风险：" + "; ".join(risks[:3]) + "。工艺参数需要根本性重新设计。",
            "confidence": "High",
        })
        predictions.append({
            "domain": "Quality / 质量",
            "prediction": "High probability (> 70%) of weld rejection if parameters unchanged. First-article testing strongly advised.",
            "prediction_cn": "如果参数不变，焊缝不合格概率高（> 70%）。强烈建议进行首件测试。",
            "recommendation": "Derate design stress or change welding process entirely.",
            "recommendation_cn": "降低设计应力或完全更换焊接工艺。",
        })
    elif risk_level == "Acceptable":
        inferences.append({
            "domain": "Process→Quality / 工艺→质量",
            "finding": "All physics domains within acceptable ranges. Process is robust for the selected material and environment.",
            "finding_cn": "所有物理领域均在可接受范围内。工艺对所选材料和环境具有良好的稳健性。",
            "confidence": "Moderate",
        })


def _position_effects(weld, f, m, inferences, predictions):
    """Weld position and torch angle effects on fluid flow and mechanical outcome."""
    joint = weld.joint
    params = weld.parameters
    pool = f.get("pool_geometry", {})
    
    if joint.position.value in ("3G", "4G", "5G", "6G"):
        inferences.append({
            "domain": "Position→Fluid / 位置→流体",
            "finding": f"{joint.position.value} position: gravity opposes Marangoni flow direction. Pool sag and irregular bead shape expected if heat input too high.",
            "finding_cn": f"{joint.position.value}位置：重力与马兰戈尼流方向相反。如果热输入过高，预期出现熔池下垂和焊道形状不规则。",
            "confidence": "High",
        })
        predictions.append({
            "domain": "Position→Mechanical / 位置→力学",
            "prediction": "Out-of-position welding: 15-25% reduction in effective joint strength due to potential lack of fusion at upper sidewall.",
            "prediction_cn": "非平焊位置焊接：由于上侧壁可能未熔合，有效接头强度降低15-25%。",
            "recommendation": "Reduce heat input by 10-15%. Increase travel speed. Use smaller electrode diameter.",
            "recommendation_cn": "热输入降低10-15%。提高焊接速度。使用更小直径的焊条。",
        })
    
    if params.torch_angle != 90:
        ang = params.torch_angle
        inferences.append({
            "domain": "Angle→Fluid / 角度→流体",
            "finding": f"Torch angle {ang}°: asymmetric arc force distribution. Arc pressure vector shifts, modifying pool shape and penetration profile.",
            "finding_cn": f"焊枪角度{ang}°：电弧力分布不对称。电弧压力矢量偏移，改变熔池形状和熔透轮廓。",
            "confidence": "Moderate",
        })
    
    if params.travel_angle != 0:
        inferences.append({
            "domain": "Angle→Thermal / 角度→热",
            "finding": f"Travel/push angle {params.travel_angle}° modifies preheating effect ahead of the arc, affecting cooling rate and bead shape.",
            "finding_cn": f"行走/推角{params.travel_angle}°改变电弧前方的预热效果，影响冷却速率和焊道形状。",
            "confidence": "Moderate",
        })
