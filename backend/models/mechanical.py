"""Mechanical analysis: residual stress, weld strength, distortion."""
import math
from ..data.weld_data import WeldParameters, WeldJoint, MaterialSpec

def residual_stress_estimate(mat: MaterialSpec, params: WeldParameters, joint: WeldJoint) -> dict:
    E=mat.youngs_modulus; alpha=mat.cte
    Tm_K=mat.melting_point+273.15; Tsol_K=0.8*Tm_K
    T_amb=params.preheat_temp+273.15; delta_T=Tsol_K-T_amb
    if joint.plate_thickness>20: constraint=0.85
    elif joint.plate_thickness>8: constraint=0.70
    else: constraint=0.50
    sigma_res=E*alpha*delta_T*constraint
    ratio=sigma_res/mat.yield_strength if mat.yield_strength>0 else 0
    if ratio>1.0: level="?????? - ????????"
    elif ratio>0.7: level="? - ??????"
    elif ratio>0.4: level="??"
    else: level="?"
    Q_kj=(params.arc_efficiency*params.voltage*params.current)/(params.travel_speed*1000.0)
    stiffness=E*joint.plate_thickness**3/12.0
    distortion_index=Q_kj/stiffness*1e9 if stiffness>0 else 0
    return {"estimated_residual_stress_MPa":round(sigma_res/1e6,1),
            "stress_to_yield_ratio":round(ratio,3),"stress_level":level,
            "distortion_index":round(distortion_index,4),
            "thermal_strain":round(alpha*delta_T,6),"constraint_factor":constraint}

def weld_strength_prediction(base: MaterialSpec, filler: MaterialSpec, joint: WeldJoint) -> dict:
    fy=filler.yield_strength/1e6; by=base.yield_strength/1e6
    bt=base.tensile_strength/1e6; ft=filler.tensile_strength/1e6
    if joint.joint_type.value=="butt":
        if fy>=by*0.9: joint_eff=0.95
        else: joint_eff=fy/by
    elif joint.joint_type.value in ("lap","tee"): joint_eff=0.75
    else: joint_eff=0.80
    py=fy*joint_eff; pt=ft*joint_eff
    if joint.plate_thickness>25: sf=1.5
    elif joint.plate_thickness>10: sf=1.3
    else: sf=1.2
    return {"joint_efficiency":round(joint_eff,3),"predicted_yield_strength_MPa":round(py,1),
            "predicted_tensile_strength_MPa":round(pt,1),"suggested_safety_factor":sf,
            "design_strength_MPa":round(py/sf,1),"base_yield_MPa":round(by,1),"filler_yield_MPa":round(fy,1)}

def distortion_analysis(params: WeldParameters, mat: MaterialSpec, joint: WeldJoint) -> dict:
    Q_kj_mm=(params.arc_efficiency*params.voltage*params.current)/(params.travel_speed*1e6)
    alpha=mat.cte; rho=mat.density; Cp=mat.specific_heat
    cross_section=joint.plate_thickness*25.0
    long_shrinkage=alpha*Q_kj_mm*1e6/(rho*Cp*cross_section)
    if joint.joint_type.value=="butt" and joint.groove_type in ("V","U"):
        beta_deg=alpha*Q_kj_mm*1e6*joint.bevel_angle/(5000*joint.plate_thickness**2)
    else: beta_deg=alpha*Q_kj_mm*1e6/(10000*joint.plate_thickness**2)
    slenderness=joint.plate_thickness/1000.0
    if slenderness<0.003: buckling_risk="High"
    elif slenderness<0.008: buckling_risk="??"
    else: buckling_risk="?"
    return {"longitudinal_shrinkage_strain":round(long_shrinkage,8),
            "angular_distortion_deg":round(beta_deg,4),"buckling_risk":buckling_risk,
            "heat_input_kJ_per_mm":round(Q_kj_mm,4)}
