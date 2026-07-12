"""Report generator: creates structured analysis reports."""
from datetime import datetime
from ..data.weld_data import WeldInput
from .predictor import run_full_analysis, predict_weld_quality

def generate_report(weld: WeldInput, format: str="markdown") -> str:
    """Generate a comprehensive analysis report in markdown or plain text."""
    analysis = run_full_analysis(weld)
    quality = predict_weld_quality(weld)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append(f"# ??????")
    lines.append(f"**????**: {now}")
    lines.append(f"**????**: {weld.id or 'N/A'}")
    lines.append("")

    # Quality overview
    lines.append("## ????")
    lines.append(f"- **??**: {quality['quality_score']}/100  **Grade**: {quality['grade']}")
    lines.append(f"- **????**: {quality['interpretation']}")
    if quality["deductions"]:
        lines.append("- **???**:")
        for d in quality["deductions"]:
            lines.append(f"  - {d}")
    lines.append("")

    # Material
    m = analysis["material"]
    lines.append("## ????")
    lines.append(f"- ??: {m['base_material']} ({m['base_grade']})")
    lines.append(f"- ????: {m['filler_material']}")
    lines.append(f"- ???: {m['carbon_equivalent']}")
    lines.append(f"- ?????: {m['weldability']['cracking_risk']}")
    lines.append(f"- ????: {m['weldability']['suggested_preheat_C']} C")
    if "filler_compatibility" in m:
        fc = m["filler_compatibility"]
        lines.append(f"- ??????: {fc['overall']}")
    lines.append("")

    # Thermal
    t = analysis["thermal"]
    lines.append("## ????")
    lines.append(f"- ???: {t['heat_input']['net_heat_input_kJ_per_mm']} kJ/mm")
    lines.append(f"- ????: {t['heat_input']['arc_power_W']} W")
    lines.append(f"- t8/5 ????: {t['cooling']['t8_5_seconds']} s ({t['cooling']['cooling_regime']})")
    lines.append(f"- ????: {t['cooling']['microstructure_prediction']}")
    lines.append(f"- ??????: {t['haz']['estimated_haz_width_mm']} mm")
    lines.append("")

    # Mechanical
    me = analysis["mechanical"]
    lines.append("## ????")
    lines.append(f"- ????: {me['residual_stress']['estimated_residual_stress_MPa']} MPa ({me['residual_stress']['stress_level']})")
    lines.append(f"- ??????: {me['weld_strength']['predicted_yield_strength_MPa']} MPa")
    lines.append(f"- ????: {me['weld_strength']['joint_efficiency']}")
    lines.append(f"- ???? (????={me['weld_strength']['suggested_safety_factor']}): {me['weld_strength']['design_strength_MPa']} MPa")
    lines.append(f"- ????: {me['distortion']['buckling_risk']}")
    lines.append(f"- ???: {me['distortion']['angular_distortion_deg']} deg")
    lines.append("")

    # Fluid
    f = analysis["fluid"]
    lines.append("## ?????")
    lines.append(f"- Marangoni ?: {f['marangoni']['marangoni_number']}")
    lines.append(f"- ??: {f['marangoni']['flow_regime']}")
    lines.append(f"- ????: {f['marangoni']['flow_direction']}")
    lines.append(f"- ????: {f['pool_geometry']['pool_width_mm']} mm")
    lines.append(f"- ????: {f['pool_geometry']['pool_depth_mm']} mm")
    lines.append("")

    # EM
    em = analysis["electromagnetic"]
    lines.append("## ????")
    lines.append(f"- Lorentz ???: {em['lorentz']['lorentz_force_density_N_per_m3']} N/m3")
    lines.append(f"- ????: {em['lorentz']['arc_pressure_Pa']} Pa")
    lines.append(f"- ?????: {em['arc_blow']['arc_blow_risk_level']}")
    lines.append(f"- ????: {em['em_stirring']['em_stirring_assessment']}")
    lines.append("")

    # Environmental
    env_a = analysis["environmental"]
    lines.append("## ????")
    lines.append(f"- ????: {weld.environment.value}")
    lines.append(f"- ????: {env_a['corrosion']['corrosion_rate_mm_per_year']} mm/year")
    lines.append(f"- ????: {env_a['corrosion']['risk_level']}")
    lines.append(f"- ????: {env_a['service_life']['estimated_service_life_years']} years")
    if env_a['service_life'].get('dbtt_note'):
        lines.append(f"- DBTT Note: {env_a['service_life']['dbtt_note']}")
    lines.append(f"- ??????: {env_a['hydrogen_cracking']['hicc_risk']}")
    lines.append(f"- ????: {env_a['fatigue']['estimated_life_years']} years ({env_a['fatigue']['life_regime']})")
    lines.append("")

    # Recommendations
    s = analysis["summary"]
    lines.append("## ????")
    for r in s["key_recommendations"]:
        lines.append(f"- {r}")

    return "\n".join(lines)
