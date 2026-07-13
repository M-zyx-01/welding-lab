"""Thermal analysis: heat input, Rosenthal solutions, cooling rates, HAZ."""
import math
from ..data.weld_data import WeldParameters, MaterialSpec

def heat_input(params: WeldParameters) -> dict:
    power = params.voltage * params.current
    q_kj_mm = (params.arc_efficiency * power) / (params.travel_speed * 1000.0)
    if params.electrode_diameter and params.electrode_diameter > 0:
        area = math.pi * (params.electrode_diameter/2.0)**2
        energy_density = power / area
    else:
        energy_density = None
    return {"net_heat_input_kJ_per_mm":round(q_kj_mm,6),"arc_power_W":round(power,1),
            "energy_density_W_per_mm2":round(energy_density,1) if energy_density else None}

def rosenthal_2d(params: WeldParameters, mat: MaterialSpec, thickness: float,
                 x: float=0.0, y: float=5.0) -> dict:
    T0 = params.preheat_temp + 273.15
    k = mat.thermal_conductivity; rho = mat.density; Cp = mat.specific_heat
    alpha = k/(rho*Cp); v = params.travel_speed/1000.0
    Q_net = params.arc_efficiency * params.voltage * params.current
    d_m = thickness/1000.0; x_m = x/1000.0; y_m = y/1000.0
    r = math.sqrt(x_m**2 + y_m**2)
    if r < 1e-9 or alpha < 1e-15: return {"error":"??????"}
    prefactor = Q_net/(2.0*math.pi*k*d_m); arg = v*r/(2.0*alpha)
    if arg < 2.0: k0 = -math.log(arg/2.0) - 0.5772156649
    else: k0 = math.sqrt(math.pi/(2.0*arg))*math.exp(-arg)
    exp_term = math.exp(-v*x_m/(2.0*alpha))
    T_peak = T0 + prefactor*exp_term*k0; T_peak_C = T_peak - 273.15
    if T_peak > T0+1: cooling_rate = 2.0*math.pi*k*rho*Cp*(d_m/Q_net)**2*v*(T_peak-T0)**3
    else: cooling_rate = 0.0
    return {"peak_temperature_C":round(T_peak_C,1),"cooling_rate_K_per_s":round(cooling_rate,2),
            "thermal_diffusivity_m2_per_s":round(alpha,10),"distance_mm":round(r*1000,2)}

def cooling_rate_t800_t500(params: WeldParameters, mat: MaterialSpec, thickness: float) -> dict:
    """t8/5 cooling time using heat-per-unit-length (J/mm) formulation."""
    T0 = params.preheat_temp
    Q_net = params.arc_efficiency * params.voltage * params.current  # W
    v_mm_s = params.travel_speed  # mm/s
    q_j_per_mm = Q_net / v_mm_s if v_mm_s > 0 else 0  # J/mm
    k_w_per_mmK = mat.thermal_conductivity / 1000.0  # W/(mm*K)
    rho_kg_per_mm3 = mat.density / 1e9  # kg/mm3
    Cp = mat.specific_heat  # J/(kg*K)
    d_mm = thickness  # mm
    delta_T = max(800.0 - T0, 1.0)
    crit_thickness = math.sqrt(q_j_per_mm / (2.0 * rho_kg_per_mm3 * Cp * delta_T))
    if d_mm <= crit_thickness:
        factor = q_j_per_mm**2 / (4.0 * math.pi * rho_kg_per_mm3 * Cp * k_w_per_mmK * d_mm**2)
        t85 = factor * (1.0/max(500.0-T0,1.0)**2 - 1.0/max(800.0-T0,1.0)**2)
        regime = "?? (??)"
    else:
        factor = q_j_per_mm / (2.0 * math.pi * k_w_per_mmK)
        t85 = factor * (1.0/max(500.0-T0,1.0) - 1.0/max(800.0-T0,1.0))
        regime = "?? (??)"
    if t85 < 3: micro = "???????? (??????)"
    elif t85 < 10: micro = "??????/???????"
    elif t85 < 30: micro = "????????-???/???"
    else: micro = "????????-??? (????)"
    return {"t8_5_seconds":round(t85,2),"cooling_regime":regime,
            "critical_thickness_mm":round(crit_thickness,2),"microstructure_prediction":micro}

def haz_width_estimate(params: WeldParameters, mat: MaterialSpec) -> dict:
    Q_kj_mm = (params.arc_efficiency*params.voltage*params.current)/(params.travel_speed*1e6)
    alpha = mat.thermal_conductivity/(mat.density*mat.specific_heat)
    if params.travel_speed>0:
        arc_time = (params.arc_length/1000.0)/(params.travel_speed/1000.0)
        diff_length = math.sqrt(alpha*arc_time)*1000
    else: diff_length=0
    if Q_kj_mm<0.5: haz_mm=1.0+3.0*Q_kj_mm
    elif Q_kj_mm<2.0: haz_mm=2.5+1.5*Q_kj_mm
    else: haz_mm=5.5+0.5*Q_kj_mm
    if mat.density<5000: haz_mm*=1.5
    if mat.composition.get("Cr",0)>10: haz_mm*=0.7
    return {"estimated_haz_width_mm":round(haz_mm,2),"thermal_diffusion_length_mm":round(diff_length,2),
            "heat_input_kJ_per_mm":round(Q_kj_mm,4)}

def peak_temperature_distribution(params: WeldParameters, mat: MaterialSpec,
                                   thickness: float, distances_mm=None) -> list:
    if distances_mm is None: distances_mm=[1.0,2.0,3.0,5.0,8.0,12.0,20.0]
    T0=params.preheat_temp+273.15; Q_net=params.arc_efficiency*params.voltage*params.current
    rho=mat.density; Cp=mat.specific_heat; d_m=thickness/1000.0; v_ms=params.travel_speed/1000.0
    melting_K=mat.melting_point+273.15
    results=[]
    for y_mm in distances_mm:
        y_m=y_mm/1000.0
        if y_m<1e-6: Tp=T0+2000
        else: Tp=T0+(Q_net/(rho*Cp*d_m*v_ms))*(1.0/(math.sqrt(2.0*math.pi*math.e)*y_m))
        Tp_C=min(Tp-273.15,melting_K-273.15+100)
        results.append({"distance_from_center_mm":round(y_mm,1),"peak_temperature_C":round(Tp_C,1)})
    return results
