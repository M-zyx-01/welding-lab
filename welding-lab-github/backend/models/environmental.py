"""Environmental assessment: corrosion, service life, hydrogen cracking, fatigue."""
import math
from ..data.weld_data import Environment, WeldParameters, MaterialSpec, WeldJoint

def corrosion_rate_estimate(mat: MaterialSpec, env: Environment) -> dict:
    is_ss = mat.composition.get("Cr", 0) > 10
    is_al = mat.density < 5000
    has_mo = mat.composition.get("Mo", 0) > 1.0
    is_ti = mat.composition.get("Ti", 0) > 50
    if env == Environment.COASTAL:
        if is_ss and has_mo:
            rate = 0.01; mech = "Pitting/crevice (Mo-enhanced passivation)"; risk = "Low"
        elif is_ss:
            rate = 0.05; mech = "Pitting/crevice corrosion"; risk = "Moderate"
        elif is_al:
            rate = 0.02; mech = "Pitting under chloride attack"; risk = "Low-Moderate"
        elif is_ti:
            rate = 0.001; mech = "Immune to chloride attack"; risk = "Negligible"
        else:
            rate = 0.15; mech = "Uniform corrosion + pitting"; risk = "High"
    elif env == Environment.UNDERWATER:
        if is_ss and has_mo:
            rate = 0.02; mech = "Crevice corrosion at depth"; risk = "Low-Moderate"
        elif is_al:
            rate = 0.03; mech = "Galvanic + pitting corrosion"; risk = "Moderate"
        elif is_ti:
            rate = 0.0005; mech = "Immune underwater"; risk = "Negligible"
        else:
            rate = 0.30; mech = "Severe general corrosion"; risk = "Very High"
    elif env == Environment.ULTRA_LOW_TEMP:
        rate = 0.001; mech = "Corrosion slowed; brittle fracture concern"; risk = "Low (corrosion); check DBTT"
    elif env == Environment.ULTRA_HIGH_TEMP:
        if is_ss:
            rate = 0.05; mech = "Oxidation/carburization"; risk = "Moderate"
        elif is_ti:
            rate = 0.02; mech = "Oxidation above 400C"; risk = "Moderate"
        else:
            rate = 0.20; mech = "Rapid oxidation scaling"; risk = "High"
    elif env == Environment.CORROSIVE_CHEMICAL:
        if is_ss and has_mo:
            rate = 0.03; mech = "Depends on chemical; Mo improves resistance"; risk = "Moderate"
        else:
            rate = 0.50; mech = "Chemical attack severe"; risk = "Very High"
    elif env == Environment.INLAND:
        if is_ss and has_mo:
            rate = 0.003; mech = "General atmospheric (low); Mo-enhanced passivation"; risk = "Low"
        elif is_ss:
            rate = 0.005; mech = "Urban/industrial atmospheric"; risk = "Low"
        elif is_al:
            rate = 0.001; mech = "Natural passivation; minimal attack"; risk = "Negligible"
        elif is_ti:
            rate = 0.0003; mech = "Excellent inland corrosion resistance"; risk = "Negligible"
        else:
            rate = 0.04; mech = "Rusting in humid/industrial air; periodic recoating needed"; risk = "Low-Moderate"
    elif env == Environment.DEEP_SEA:
        if is_ss and has_mo:
            rate = 0.03; mech = "Pitting/crevice corrosion at depth with high pressure"; risk = "Moderate"
        elif is_ti:
            rate = 0.001; mech = "Ti immune even at extreme depths"; risk = "Negligible"
        elif is_al:
            rate = 0.08; mech = "Al galvanic corrosion accelerates under hydrostatic pressure"; risk = "High"
        else:
            rate = 0.45; mech = "Accelerated general corrosion + pitting under hydrostatic pressure"; risk = "Very High"
    elif env == Environment.SPACE:
        if is_ti:
            rate = 0.0001; mech = "Vacuum-stable; negligible outgassing"; risk = "Negligible"
        elif is_ss:
            rate = 0.001; mech = "Vacuum stable; atomic oxygen erosion at LEO"; risk = "Low"
        elif is_al:
            rate = 0.005; mech = "Outgassing concern; thermal cycling stress"; risk = "Low-Moderate"
        else:
            rate = 0.01; mech = "Vacuum outgassing + thermal cycling + atomic oxygen (LEO)"; risk = "Moderate"
    elif env == Environment.NUCLEAR:
        if is_ss:
            rate = 0.005; mech = "IASCC + irradiation embrittlement"; risk = "Low-Moderate"
        else:
            rate = 0.05; mech = "Irradiation-assisted corrosion"; risk = "Moderate"
    else:
        rate = 0.005; mech = "Standard indoor conditions"; risk = "Low"
    return {"corrosion_rate_mm_per_year": round(rate, 4), "mechanism": mech, "risk_level": risk, "environment": env.value}


def service_life_estimate(mat: MaterialSpec, env: Environment, joint: WeldJoint,
                           critical_thickness_loss_mm: float = 2.0) -> dict:
    corr = corrosion_rate_estimate(mat, env)
    rate = corr["corrosion_rate_mm_per_year"]
    years = critical_thickness_loss_mm / rate if rate > 1e-9 else 100.0
    if env == Environment.SPACE:
        dbtt = "Thermal cycling (-150 to +150 C per orbit). CTE mismatch induces fatigue. Vacuum welding quality critical."
    elif env == Environment.DEEP_SEA:
        dbtt = "Hydrostatic pressure reduces fatigue crack growth rate but increases corrosion-fatigue coupling. Check HISC."
    elif env == Environment.ULTRA_LOW_TEMP:
        dbtt = "For ferritic steels, check DBTT. Estimated DBTT shift near weld: +20 C. Service at low temp may cause brittle fracture."
    else:
        dbtt = None
    return {"estimated_service_life_years": round(years, 1), "corrosion_rate_mm_per_year": rate,
            "critical_thickness_loss_mm": critical_thickness_loss_mm, "dbtt_note": dbtt}


def hydrogen_cracking_risk(mat: MaterialSpec, params: WeldParameters, env: Environment) -> dict:
    comp = mat.composition
    ce = comp.get("C", 0) + comp.get("Mn", 0) / 6 + (comp.get("Cr", 0) + comp.get("Mo", 0) + comp.get("V", 0)) / 5 + (comp.get("Ni", 0) + comp.get("Cu", 0)) / 15
    Q_kj_mm = (params.arc_efficiency * params.voltage * params.current) / (params.travel_speed * 1e6)
    ce_risk = "High" if ce > 0.5 else ("Moderate" if ce > 0.35 else "Low")
    if Q_kj_mm < 0.5:
        heat_risk = "High (fast cooling)"
    elif Q_kj_mm < 1.5:
        heat_risk = "Moderate"
    else:
        heat_risk = "Low (slow cooling)"
    if env in (Environment.UNDERWATER, Environment.COASTAL, Environment.DEEP_SEA, Environment.HIGH_HUMIDITY, Environment.CORROSIVE_CHEMICAL):
        h_src = "High (moisture/environment)"
    else:
        h_src = "Low"
    score = 0
    if ce_risk == "High":
        score += 4
    elif ce_risk == "Moderate":
        score += 2
    if heat_risk.startswith("High"):
        score += 3
    elif heat_risk == "Moderate":
        score += 1
    if h_src.startswith("High"):
        score += 3
    if score >= 7:
        overall = "Severe"
    elif score >= 4:
        overall = "High"
    elif score >= 2:
        overall = "Moderate"
    else:
        overall = "Low"
    mitigations = (["Low-hydrogen electrodes (H4/H8)",
                    f"Preheat to {params.preheat_temp + 100 if params.preheat_temp < 200 else 300} C",
                    "Post-weld heat treatment", "Maintain interpass > 250C for >2h"]
                   if overall in ("Severe", "High") else ["Standard low-hydrogen practice", "Avoid moisture contamination"])
    return {"hicc_risk": overall, "risk_score": score, "carbon_equivalent_risk": ce_risk,
            "cooling_rate_risk": heat_risk, "hydrogen_source_risk": h_src, "mitigations": mitigations}


def fatigue_life_estimate(mat: MaterialSpec, env: Environment, stress_range_MPa: float = 100.0,
                           cycles_per_year: float = 1e6) -> dict:
    # Base fatigue limit estimate from tensile strength
    if mat.tensile_strength > 800e6:
        fl = mat.tensile_strength / 1e6 * 0.45
    elif mat.tensile_strength > 400e6:
        fl = mat.tensile_strength / 1e6 * 0.40
    else:
        fl = mat.tensile_strength / 1e6 * 0.35
    # Environment derating factors
    if env == Environment.COASTAL:
        fl *= 0.70
    elif env == Environment.UNDERWATER:
        fl *= 0.65
    elif env == Environment.DEEP_SEA:
        fl *= 0.55
    elif env == Environment.CORROSIVE_CHEMICAL:
        fl *= 0.50
    elif env == Environment.ULTRA_HIGH_TEMP:
        fl *= 0.55
    elif env == Environment.ULTRA_LOW_TEMP:
        fl *= 1.05
    elif env == Environment.INLAND:
        fl *= 0.90
    elif env == Environment.SPACE:
        fl *= 0.80
    elif env == Environment.HIGH_HUMIDITY:
        fl *= 0.85
    elif env == Environment.VACUUM:
        fl *= 0.95
    elif env == Environment.NUCLEAR:
        fl *= 0.75
    # else: indoor_standard, no derating (fl *= 1.0 implicit)
    if stress_range_MPa <= fl:
        N = 1e12
        life_years = N / cycles_per_year
        regime = "Infinite life (below fatigue limit)"
    else:
        m = 3.0
        C = (mat.tensile_strength / 1e6 * 2) ** m * 1e6
        N = C / (stress_range_MPa ** m)
        life_years = N / cycles_per_year
        regime = "Finite life"
    derating = round(fl / (mat.tensile_strength / 1e6 * 0.40), 2) if mat.tensile_strength > 0 else 1
    return {"fatigue_limit_MPa": round(fl, 1), "stress_range_MPa": stress_range_MPa,
            "estimated_cycles_to_failure": round(N, 0), "estimated_life_years": round(min(life_years, 1000.0), 1),
            "life_regime": regime, "environment_derating_factor": derating}
