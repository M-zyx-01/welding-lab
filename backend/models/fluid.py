"""Fluid dynamics: Marangoni convection, weld pool geometry, buoyancy."""
import math
from ..data.weld_data import WeldParameters, MaterialSpec

def marangoni_number(params: WeldParameters, mat: MaterialSpec) -> dict:
    s_content=mat.composition.get("S",0.0)
    if s_content>0.01:
        d_gamma_dT=0.2e-3; flow_direction="???? (??????)"
    else:
        d_gamma_dT=-0.35e-3; flow_direction="???? (??????)"
    L=params.arc_length*2.0/1000.0
    delta_T=mat.melting_point*0.3
    if mat.density<5000: mu=1.2e-3
    elif mat.composition.get("Ti",0)>50: mu=5.0e-3
    else: mu=5.5e-3
    alpha=mat.thermal_conductivity/(mat.density*mat.specific_heat)
    Ma=abs(d_gamma_dT)*delta_T*L/(mu*alpha) if mu*alpha>0 else 0
    rho=mat.density; v_char=abs(d_gamma_dT)*delta_T/mu
    Re=rho*v_char*L/mu if mu>0 else 0
    if Re<10: regime="?? (??)"
    elif Re<100: regime="??"
    elif Re<1000: regime="???"
    else: regime="??"
    return {"marangoni_number":round(Ma,2),"reynolds_number":round(Re,1),
            "flow_regime":regime,"flow_direction":flow_direction,
            "surface_tension_gradient_N_per_mK":d_gamma_dT,
            "characteristic_velocity_m_per_s":round(v_char,6),"dynamic_viscosity_Pa_s":mu}

def weld_pool_geometry(params: WeldParameters, mat: MaterialSpec) -> dict:
    Q_kj_mm=(params.arc_efficiency*params.voltage*params.current)/(params.travel_speed*1e6)
    Tm=mat.melting_point; k=mat.thermal_conductivity; rho=mat.density; Cp=mat.specific_heat
    pool_width=2.0*math.sqrt((Q_kj_mm*1e6)/(math.pi*k*Tm*10)) if Tm>0 else 0
    if params.travel_speed>0 and Tm>0:
        pool_length=(params.arc_efficiency*params.voltage*params.current)/((params.travel_speed/1000.0)*rho*Cp*Tm)*1000
        pool_length=min(pool_length, pool_width*3)
    else: pool_length=0
    pool_depth=pool_width*0.3
    wdr=pool_width/pool_depth if pool_depth>0 else 0
    return {"pool_width_mm":round(pool_width,2),"pool_length_mm":round(pool_length,2),
            "pool_depth_mm":round(pool_depth,2),"width_to_depth_ratio":round(wdr,1),
            "pool_area_mm2":round(math.pi*pool_width*pool_length/4.0,1)}

def buoyancy_effect(params: WeldParameters, mat: MaterialSpec) -> dict:
    g=9.81; beta_thermal=1.0/(mat.melting_point+273.15)
    delta_T=mat.melting_point*0.3; L=params.arc_length*2.0/1000.0
    mu=1.2e-3 if mat.density<5000 else 5.5e-3
    nu=mu/mat.density; Gr=g*beta_thermal*delta_T*L**3/(nu**2) if nu>0 else 0
    return {"grashof_number":round(Gr,1),"kinematic_viscosity_m2_per_s":round(nu,10),
            "buoyancy_note":"??????????????? Marangoni ??"}
