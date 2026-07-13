"""Electromagnetic effects: arc physics, Lorentz force, arc blow, EM stirring."""
import math
from ..data.weld_data import WeldParameters, WeldJoint, MaterialSpec

def lorentz_force(params: WeldParameters) -> dict:
    mu0=4e-7*math.pi; I=params.current
    if params.electrode_diameter: r_arc=params.electrode_diameter/2.0/1000.0
    else: r_arc=params.arc_length/2.0/1000.0
    if r_arc<1e-6: return {"error":"Arc radius too small"}
    J=I/(math.pi*r_arc**2); B_self=mu0*I/(2.0*math.pi*r_arc)
    F_L=J*B_self; p_arc=mu0*I**2/(8.0*math.pi**2*r_arc**2)
    stiffness=mu0*I**2/(4.0*math.pi**2*r_arc**3) if r_arc>0 else 0
    return {"current_density_A_per_m2":round(J,0),"self_magnetic_field_T":round(B_self,6),
            "lorentz_force_density_N_per_m3":round(F_L,0),"arc_pressure_Pa":round(p_arc,1),
            "arc_stiffness_N_per_m4":round(stiffness,0),"arc_radius_estimate_mm":round(r_arc*1000,3)}

def magnetic_arc_blow_risk(params: WeldParameters, joint: WeldJoint, mat: MaterialSpec) -> dict:
    risk_score=0; risk_factors=[]
    if params.polarity.upper() in ("DCEN","DCEP"):
        risk_score+=2; risk_factors.append("??????????")
    else: risk_factors.append("???? - ???????")
    mu_r=mat.magnetic_permeability
    if mu_r>10: risk_score+=3; risk_factors.append(f"????? (mu_r={mu_r})")
    elif mu_r>2: risk_score+=1; risk_factors.append("????")
    if params.current>250: risk_score+=2; risk_factors.append("??? > 250 A")
    elif params.current>150: risk_score+=1
    if joint.joint_type.value in ("corner","tee"):
        risk_score+=1; risk_factors.append("???????")
    if risk_score>=6:
        level="Severe"; mitigations=["???????","??????","???????","???????????"]
    elif risk_score>=4:
        level="Moderate"; mitigations=["?????????","??????","???????????"]
    elif risk_score>=2: level="Low"; mitigations=["??????","????"]
    else: level="Negligible"; mitigations=[]
    return {"arc_blow_risk_level":level,"risk_score":risk_score,"risk_factors":risk_factors,"mitigations":mitigations}

def electromagnetic_stirring(params: WeldParameters, mat: MaterialSpec) -> dict:
    mu0=4e-7*math.pi
    if params.electrode_diameter: r_arc=params.electrode_diameter/2.0/1000.0
    else: r_arc=params.arc_length/2.0/1000.0
    I=params.current; B=mu0*I/(2.0*math.pi*r_arc) if r_arc>1e-6 else 0
    sigma_el=1.0/mat.electrical_resistivity if mat.electrical_resistivity>0 else 0
    mu=1.2e-3 if mat.density<5000 else 5.5e-3
    Ha=B*r_arc*math.sqrt(sigma_el/mu) if mu>0 else 0
    if Ha>10: stirring="????? - ??????"
    elif Ha>1: stirring="??????"
    else: stirring="?????"
    return {"hartmann_number":round(Ha,3),"magnetic_field_T":round(B,6),
            "electrical_conductivity_S_per_m":round(sigma_el,0),"em_stirring_assessment":stirring}
