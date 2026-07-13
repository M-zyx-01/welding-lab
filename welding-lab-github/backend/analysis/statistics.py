"""
Statistical analysis: trend detection, correlation, outlier detection.
统计分析：趋势检测、相关性分析、异常值检测。
"""
import math
from typing import List, Dict, Optional, Any
from collections import Counter


def correlation_matrix(experiments: List[dict]) -> dict:
    """Compute Pearson correlation between key numerical parameters.
    计算关键数值参数之间的Pearson相关系数矩阵。"""
    params_of_interest = [
        ("current_A", "Current / 电流"),
        ("voltage_V", "Voltage / 电压"),
        ("travel_speed_mm_s", "Travel Speed / 速度"),
        ("preheat_temp_C", "Preheat / 预热"),
        ("plate_thickness_mm", "Thickness / 板厚"),
        ("quality_score", "Quality Score / 质量分数"),
        ("heat_input_kJ_mm", "Heat Input / 热输入"),
        ("haz_width_mm", "HAZ Width / HAZ宽度"),
        ("residual_stress_MPa", "Residual Stress / 残余应力"),
        ("service_life_years", "Service Life / 服役寿命"),
        ("corrosion_rate_mm_yr", "Corrosion Rate / 腐蚀速率"),
    ]
    # Extract data
    available = []
    for key, label in params_of_interest:
        vals = []
        for exp in experiments:
            v = exp.get(key)
            if v is not None and isinstance(v, (int, float)):
                vals.append(v)
        if len(vals) >= 3:
            available.append((key, label, vals))
    if len(available) < 2:
        return {"error": "Insufficient data for correlation analysis / 数据不足无法进行相关性分析"}
    # Compute correlation matrix
    n = len(available)
    matrix = []
    significant_pairs = []
    for i in range(n):
        row = []
        for j in range(n):
            r = _pearson_r(available[i][2], available[j][2])
            row.append(round(r, 3))
            if i < j and abs(r) > 0.5:
                significant_pairs.append({
                    "param1": available[i][1],
                    "param2": available[j][1],
                    "correlation": round(r, 3),
                    "strength": "Strong" if abs(r) > 0.8 else "Moderate",
                    "strength_cn": "强" if abs(r) > 0.8 else "中等",
                    "direction": "Positive / 正相关" if r > 0 else "Negative / 负相关",
                })
        matrix.append(row)
    return {
        "parameters": [a[1] for a in available],
        "parameter_keys": [a[0] for a in available],
        "correlation_matrix": matrix,
        "significant_correlations": sorted(significant_pairs, key=lambda x: abs(x["correlation"]), reverse=True),
    }


def _pearson_r(x: List[float], y: List[float]) -> float:
    """Pearson correlation coefficient."""
    n = min(len(x), len(y))
    if n < 3:
        return 0.0
    x = x[:n]; y = y[:n]
    mx = sum(x) / n; my = sum(y) / n
    sx = math.sqrt(sum((v - mx) ** 2 for v in x))
    sy = math.sqrt(sum((v - my) ** 2 for v in y))
    if sx < 1e-15 or sy < 1e-15:
        return 0.0
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    return cov / (sx * sy)


def trend_analysis(experiments: List[dict]) -> dict:
    """Detect trends in quality score over time or sequence.
    检测质量分数随时间或序列的趋势。"""
    scored = [(i, exp.get("quality_score")) for i, exp in enumerate(experiments)
              if exp.get("quality_score") is not None]
    if len(scored) < 3:
        return {"error": "Need at least 3 scored experiments / 需要至少3个有评分的实验"}
    xs = [float(s[0]) for s in scored]
    ys = [float(s[1]) for s in scored]
    n = len(xs)
    r = _pearson_r(xs, ys)
    # Linear regression slope
    mx = sum(xs) / n; my = sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = sum((x - mx) ** 2 for x in xs)
    slope = num / den if den > 0 else 0
    # Trend assessment
    if abs(r) < 0.3:
        trend = "Stable / 稳定"
        trend_cn = "无明显趋势"
    elif r > 0.3:
        trend = "Improving / 改善" if slope > 0 else "Declining / 下降"
        trend_cn = "质量趋势向好" if slope > 0 else "质量趋势下滑"
    else:
        trend = "Declining / 下降"
        trend_cn = "质量趋势下滑"
    return {
        "trend": trend,
        "trend_cn": trend_cn,
        "correlation_with_sequence": round(r, 3),
        "slope_per_experiment": round(slope, 2),
        "samples": n,
        "avg_quality": round(my, 1),
    }


def outlier_detection(experiments: List[dict]) -> dict:
    """Detect outlier experiments using IQR method on quality score.
    使用IQR方法检测质量分数异常值。"""
    scores = [exp.get("quality_score") for exp in experiments
              if exp.get("quality_score") is not None]
    if len(scores) < 4:
        return {"error": "Need at least 4 scored experiments / 需要至少4个有评分的实验"}
    sorted_scores = sorted(scores)
    n = len(sorted_scores)
    q1_idx = n // 4; q3_idx = 3 * n // 4
    q1 = sorted_scores[q1_idx]; q3 = sorted_scores[q3_idx]
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr; upper = q3 + 1.5 * iqr
    outliers = []
    for exp in experiments:
        s = exp.get("quality_score")
        if s is not None and (s < lower or s > upper):
            outliers.append({
                "id": exp.get("id"),
                "exp_name": exp.get("exp_name", ""),
                "quality_score": s,
                "deviation": round(s - (q1 + q3) / 2, 1),
                "type": "Low outlier / 低异常值" if s < lower else "High outlier / 高异常值",
            })
    return {
        "q1": round(q1, 1), "q3": round(q3, 1), "iqr": round(iqr, 1),
        "lower_bound": round(lower, 1), "upper_bound": round(upper, 1),
        "outliers": outliers,
        "outlier_count": len(outliers),
        "total_samples": n,
    }


def parameter_distribution(experiments: List[dict], parameter: str) -> dict:
    """Distribution analysis for a specific parameter.
    特定参数的分布分析。"""
    param_labels = {
        "current_A": "Current (A) / 电流",
        "voltage_V": "Voltage (V) / 电压",
        "travel_speed_mm_s": "Speed (mm/s) / 速度",
        "preheat_temp_C": "Preheat (C) / 预热",
        "plate_thickness_mm": "Thickness (mm) / 板厚",
        "quality_score": "Quality Score / 质量分数",
        "heat_input_kJ_mm": "Heat Input (kJ/mm) / 热输入",
        "haz_width_mm": "HAZ Width (mm) / HAZ宽度",
        "residual_stress_MPa": "Residual Stress (MPa) / 残余应力",
        "service_life_years": "Service Life (yr) / 服役寿命",
    }
    vals = [exp.get(parameter) for exp in experiments
            if exp.get(parameter) is not None and isinstance(exp.get(parameter), (int, float))]
    if len(vals) < 2:
        return {"error": f"Insufficient data for {parameter} / 数据不足"}
    vals_sorted = sorted(vals)
    n = len(vals_sorted)
    mean_val = sum(vals_sorted) / n
    variance = sum((v - mean_val) ** 2 for v in vals_sorted) / n
    std_val = math.sqrt(variance)
    return {
        "parameter": param_labels.get(parameter, parameter),
        "count": n,
        "mean": round(mean_val, 3),
        "std_dev": round(std_val, 3),
        "min": round(vals_sorted[0], 3),
        "max": round(vals_sorted[-1], 3),
        "median": round(vals_sorted[n // 2], 3),
        "cv_percent": round(std_val / mean_val * 100, 1) if mean_val != 0 else 0,
        "histogram": _simple_histogram(vals_sorted),
    }


def _simple_histogram(values: List[float], bins: int = 10) -> List[dict]:
    """Simple histogram binning."""
    if len(values) < 2:
        return []
    vmin, vmax = values[0], values[-1]
    if vmax - vmin < 1e-9:
        return [{"range": f"{vmin:.1f}-{vmax:.1f}", "count": len(values)}]
    bin_width = (vmax - vmin) / bins
    result = []
    for i in range(bins):
        lo = vmin + i * bin_width
        hi = lo + bin_width
        cnt = sum(1 for v in values if lo <= v < hi)
        if i == bins - 1:
            cnt = sum(1 for v in values if lo <= v <= vmax)
        result.append({"range": f"{lo:.1f}-{hi:.1f}", "count": cnt})
    return result


def compare_groups(experiments: List[dict], group_by: str) -> dict:
    """Compare statistics grouped by a categorical field.
    按分类字段分组比较统计信息。"""
    valid_group_fields = {"process", "environment", "base_material", "joint_type", "quality_grade"}
    if group_by not in valid_group_fields:
        return {"error": f"Invalid group field: {group_by} / 无效的分组字段"}
    groups = {}
    for exp in experiments:
        key = exp.get(group_by, "Unknown")
        if key not in groups:
            groups[key] = []
        groups[key].append(exp)
    result = []
    for key, exps in sorted(groups.items()):
        scores = [e.get("quality_score") for e in exps if e.get("quality_score") is not None]
        haz = [e.get("haz_width_mm") for e in exps if e.get("haz_width_mm") is not None]
        life = [e.get("service_life_years") for e in exps if e.get("service_life_years") is not None]
        stress = [e.get("residual_stress_MPa") for e in exps if e.get("residual_stress_MPa") is not None]
        result.append({
            "group": key,
            "count": len(exps),
            "avg_quality": round(sum(scores) / len(scores), 1) if scores else None,
            "avg_haz_width": round(sum(haz) / len(haz), 2) if haz else None,
            "avg_service_life": round(sum(life) / len(life), 1) if life else None,
            "avg_residual_stress": round(sum(stress) / len(stress), 1) if stress else None,
        })
    return {"group_by": group_by, "groups": result}
