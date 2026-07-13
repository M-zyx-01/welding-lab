"""
Energy domain model: power density, energy balance, efficiency analysis.
能量域模型：功率密度、能量平衡、效率分析。
"""
import math
from ..data.weld_data import WeldParameters, MaterialSpec, WeldJoint, Environment


def energy_balance(params: WeldParameters, mat: MaterialSpec, joint: WeldJoint) -> dict:
    """Full energy balance: input, absorbed, losses.
    完整能量平衡：输入、吸收、损失。"""
    # Input electrical power
    P_input = params.voltage * params.current  # W
    # Arc efficiency - how much reaches workpiece
    P_workpiece = P_input * params.arc_efficiency
    # Convection loss from weld pool surface
    if params.electrode_diameter:
        pool_radius = params.electrode_diameter * 3 / 1000.0  # m, approximate
    else:
        pool_radius = 0.005  # 5mm default
    pool_area = math.pi * pool_radius ** 2
    h_conv = 25.0  # W/(m2*K) natural convection
    T_pool_K = mat.melting_point + 273.15
    T_amb_K = params.preheat_temp + 273.15
    P_convection = h_conv * pool_area * (T_pool_K - T_amb_K)
    # Radiation loss (Stefan-Boltzmann)
    sigma_sb = 5.67e-8  # W/(m2*K4)
    emissivity = 0.4
    P_radiation = emissivity * sigma_sb * pool_area * (T_pool_K**4 - T_amb_K**4)
    # Conduction into workpiece
    P_conduction = P_workpiece - P_convection - P_radiation
    if P_conduction < 0:
        P_conduction = max(P_workpiece * 0.6, 0)
    # Energy per unit length
    v_m_per_s = params.travel_speed / 1000.0
    E_per_length = P_workpiece / v_m_per_s if v_m_per_s > 0 else 0  # J/m
    # Melting efficiency
    vol_rate = pool_area * v_m_per_s  # m3/s
    rho = mat.density
    Cp = mat.specific_heat
    T_melt = mat.melting_point
    H_fusion = 2.5e5  # J/kg approximate latent heat
    P_melt = vol_rate * rho * (Cp * (T_melt - params.preheat_temp) + H_fusion)
    melting_efficiency = P_melt / P_workpiece if P_workpiece > 0 else 0
    return {
        "input_power_W": round(P_input, 1),
        "power_to_workpiece_W": round(P_workpiece, 1),
        "power_convection_W": round(P_convection, 1),
        "power_radiation_W": round(P_radiation, 1),
        "power_conduction_W": round(P_conduction, 1),
        "energy_per_length_J_per_m": round(E_per_length, 0),
        "melting_efficiency": round(melting_efficiency, 3),
        "thermal_efficiency": params.arc_efficiency,
    }


def power_density(params: WeldParameters) -> dict:
    """Power density at arc spot and energy flux.
    电弧斑点功率密度和能量通量。"""
    if params.electrode_diameter and params.electrode_diameter > 0:
        r_spot = params.electrode_diameter / 2.0 / 1000.0
    else:
        r_spot = params.arc_length / 2.0 / 1000.0
    if r_spot < 1e-6:
        return {"error": "Spot radius too small"}
    spot_area = math.pi * r_spot ** 2
    P_workpiece = params.arc_efficiency * params.voltage * params.current
    # Power density at spot
    pd_spot = P_workpiece / spot_area  # W/m2
    # Energy intensity (fluence) - energy per unit area per pass
    v_m_s = params.travel_speed / 1000.0
    t_dwell = 2.0 * r_spot / v_m_s if v_m_s > 0 else 0
    fluence = pd_spot * t_dwell  # J/m2
    # Gaussian distribution peak
    pd_peak = 2.0 * pd_spot  # Peak is 2x average for Gaussian
    # Classification
    if pd_spot > 1e10:
        regime = "Keyhole / 匙孔模式"
    elif pd_spot > 1e9:
        regime = "Transitional / 过渡模式"
    elif pd_spot > 1e8:
        regime = "Conduction / 传导模式"
    else:
        regime = "Low density / 低密度"
    return {
        "spot_radius_mm": round(r_spot * 1000, 3),
        "spot_area_mm2": round(spot_area * 1e6, 2),
        "power_density_W_per_mm2": round(pd_spot / 1e6, 1),
        "peak_power_density_W_per_mm2": round(pd_peak / 1e6, 1),
        "energy_fluence_J_per_mm2": round(fluence / 1e6, 2),
        "dwell_time_ms": round(t_dwell * 1000, 2),
        "power_regime": regime,
    }


def energy_efficiency(params: WeldParameters, mat: MaterialSpec, joint: WeldJoint) -> dict:
    """Process energy efficiency metrics.
    工艺能量效率指标。"""
    # Electrical to thermal efficiency
    P_electrical = params.voltage * params.current
    P_thermal = P_electrical * params.arc_efficiency
    # Volumetric energy density
    Q_j_per_mm = P_thermal / params.travel_speed if params.travel_speed > 0 else 0  # J/mm
    if params.electrode_diameter:
        deposit_area = math.pi * (params.electrode_diameter / 2) ** 2
    else:
        deposit_area = math.pi * 4  # default ~2mm radius
    vol_energy = Q_j_per_mm / deposit_area if deposit_area > 0 else 0  # J/mm3
    # Specific energy (energy per kg of deposited metal)
    mass_per_mm = deposit_area * 1.0 * mat.density / 1e9  # kg/mm length
    specific_energy = Q_j_per_mm / (mass_per_mm * 1000) if mass_per_mm > 0 else 0  # kJ/kg
    # Process benchmark comparison
    benchmarks = {
        "GTAW": {"typical_eff": 0.70, "typical_energy_kJ_per_mm": 0.5},
        "GMAW": {"typical_eff": 0.80, "typical_energy_kJ_per_mm": 0.6},
        "SMAW": {"typical_eff": 0.75, "typical_energy_kJ_per_mm": 0.8},
        "FCAW": {"typical_eff": 0.80, "typical_energy_kJ_per_mm": 0.7},
        "SAW": {"typical_eff": 0.95, "typical_energy_kJ_per_mm": 1.5},
        "PAW": {"typical_eff": 0.75, "typical_energy_kJ_per_mm": 0.4},
        "LBW": {"typical_eff": 0.85, "typical_energy_kJ_per_mm": 0.1},
        "EBW": {"typical_eff": 0.90, "typical_energy_kJ_per_mm": 0.08},
    }
    proc_name = params.process.value if hasattr(params.process, 'value') else str(params.process)
    bench = benchmarks.get(proc_name, {"typical_eff": 0.75, "typical_energy_kJ_per_mm": 0.5})
    eff_vs_benchmark = params.arc_efficiency / bench["typical_eff"] if bench["typical_eff"] > 0 else 1
    # Energy cost estimate (very rough)
    energy_kWh_per_m = Q_j_per_mm * 1000 / 3.6e6  # kWh per meter
    return {
        "electrical_power_W": round(P_electrical, 1),
        "thermal_power_W": round(P_thermal, 1),
        "heat_input_kJ_per_mm": round(Q_j_per_mm / 1000, 4),
        "volumetric_energy_J_per_mm3": round(vol_energy, 1),
        "specific_energy_kJ_per_kg": round(specific_energy, 1),
        "energy_per_meter_kWh": round(energy_kWh_per_m, 5),
        "efficiency_vs_benchmark": round(eff_vs_benchmark, 2),
        "benchmark_process": proc_name,
    }


def energy_intensity_distribution(params: WeldParameters, mat: MaterialSpec,
                                   distances_mm: list = None) -> list:
    """Energy intensity as function of distance from arc center.
    能量强度随距电弧中心距离的分布。"""
    if distances_mm is None:
        distances_mm = [0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0, 20.0]
    if params.electrode_diameter and params.electrode_diameter > 0:
        r_eff = params.electrode_diameter / 2.0  # mm, effective radius
    else:
        r_eff = params.arc_length / 2.0
    P_thermal = params.arc_efficiency * params.voltage * params.current
    # Gaussian distribution
    sigma = r_eff / 2.0  # standard deviation
    results = []
    for d in distances_mm:
        q_r = (P_thermal / (2.0 * math.pi * sigma**2)) * math.exp(-d**2 / (2.0 * sigma**2))
        q_r_W_per_mm2 = q_r / 1e6  # convert to W/mm2
        results.append({
            "distance_mm": round(d, 1),
            "power_density_W_per_mm2": round(q_r_W_per_mm2, 1),
            "fraction_of_peak": round(math.exp(-d**2 / (2.0 * sigma**2)), 3),
        })
    return results


def environmental_energy_impact(mat: MaterialSpec, env: Environment) -> dict:
    """Energy considerations for different service environments.
    不同服役环境下的能量考量。"""
    impacts = {
        "ultra_low_temp": {
            "thermal_conductivity_factor": 1.15,
            "note": "Higher thermal conductivity at cryogenic temperatures increases heat loss / 低温下热导率升高增加热损失",
            "energy_penalty": "5-15% more preheat energy required / 需增加5-15%预热能量",
        },
        "ultra_high_temp": {
            "thermal_conductivity_factor": 0.90,
            "note": "Reduced conductivity at high temp; radiation dominates / 高温下热导率降低；辐射主导",
            "energy_penalty": "Creep-resistant alloys typically need higher preheat / 抗蠕变合金通常需要更高预热",
        },
        "coastal": {"thermal_conductivity_factor": 1.0, "note": "Standard thermal profile / 标准热分布", "energy_penalty": "None / 无"},
        "underwater": {
            "thermal_conductivity_factor": 0.30,
            "note": "Water quenching effect dramatically increases cooling rate / 水淬效应显著增加冷却速率",
            "energy_penalty": "30-50% more heat input to compensate / 需增加30-50%热输入补偿",
        },
        "deep_sea": {
            "thermal_conductivity_factor": 0.25,
            "note": "Extreme quenching at depth; hyperbaric effects / 深海极端淬冷；超压效应",
            "energy_penalty": "50-80% more heat input; hyperbaric welding required / 需增加50-80%热输入；需高压焊接",
        },
        "space": {
            "thermal_conductivity_factor": 0.01,
            "note": "No convective cooling; radiation-only heat loss / 无对流传热；仅辐射散热",
            "energy_penalty": "Overheating risk; lower heat input needed / 过热风险；需降低热输入",
        },
        "vacuum": {
            "thermal_conductivity_factor": 0.05,
            "note": "No convective cooling; EBW preferred / 无对流传热；电子束焊优先",
            "energy_penalty": "Heat management critical / 热管理至关重要",
        },
        "nuclear": {
            "thermal_conductivity_factor": 0.95,
            "note": "Slight irradiation effect on thermal properties / 辐照对热性能有轻微影响",
            "energy_penalty": "Additional safety margin in heat input / 热输入需附加安全裕度",
        },
    }
    env_key = env.value if hasattr(env, 'value') else str(env)
    impact = impacts.get(env_key, {"thermal_conductivity_factor": 1.0, "note": "Standard / 标准", "energy_penalty": "None / 无"})
    return {
        "environment": env_key,
        "thermal_conductivity_factor": impact["thermal_conductivity_factor"],
        "note": impact["note"],
        "energy_penalty": impact["energy_penalty"],
    }
