"""
Conclusion engine: auto-derive research findings from batch experimental data.
结论引擎：从批量实验数据中自动推导研究结论。
"""
from typing import List, Dict, Optional
from .statistics import correlation_matrix, trend_analysis, outlier_detection, compare_groups


def derive_conclusions(experiments: List[dict]) -> dict:
    """Analyze batch experiments and generate structured research conclusions.
    分析批量实验数据，生成结构化研究结论。

    Returns conclusions in logical categories:
    - Key findings (关键发现)
    - Parameter relationships (参数关系)
    - Anomalies (异常发现)
    - Recommendations (研究建议)
    """
    if len(experiments) < 3:
        return {
            "summary": "Insufficient data for conclusions. Minimum 3 experiments required. / 数据不足，至少需要3个实验。",
            "summary_cn": "数据不足以生成结论，至少需要3个实验记录。",
        }

    findings: List[dict] = []
    recommendations: List[dict] = []

    # 1. Quality overview / 质量概览
    _quality_overview(experiments, findings, recommendations)

    # 2. Parameter correlations / 参数相关性
    _correlation_findings(experiments, findings)

    # 3. Environment effects / 环境效应
    _environment_findings(experiments, findings, recommendations)

    # 4. Process comparison / 工艺比较
    _process_findings(experiments, findings, recommendations)

    # 5. Trends and outliers / 趋势和异常
    _trend_outlier_findings(experiments, findings, recommendations)

    # 6. Material insights / 材料洞察
    _material_findings(experiments, findings, recommendations)

    # Generate summary
    summary = _generate_summary(findings, recommendations, experiments)

    return {
        "summary": summary["en"],
        "summary_cn": summary["cn"],
        "key_findings": findings,
        "research_recommendations": recommendations,
        "total_experiments_analyzed": len(experiments),
    }


def _quality_overview(experiments: List[dict], findings: List[dict], recommendations: List[dict]):
    scores = [e.get("quality_score") for e in experiments if e.get("quality_score") is not None]
    grades = [e.get("quality_grade") for e in experiments if e.get("quality_grade")]
    if not scores:
        return
    avg_score = sum(scores) / len(scores)
    from collections import Counter
    grade_counts = Counter(grades)
    a_pct = (grade_counts.get("A", 0) / len(grades) * 100) if grades else 0
    f_pct = (grade_counts.get("F", 0) / len(grades) * 100) if grades else 0
    level = "excellent / 优秀" if avg_score >= 85 else (
        "good / 良好" if avg_score >= 70 else (
        "moderate / 中等" if avg_score >= 55 else "poor / 较差"))
    findings.append({
        "id": "F-Q01",
        "domain": "Quality / 质量",
        "finding": f"Average quality score: {avg_score:.1f}/100 across {len(scores)} experiments.",
        "finding_cn": f"平均质量分数：{avg_score:.1f}/100，共{len(scores)}个实验。",
        "detail": f"Grade A: {a_pct:.0f}%, Grade F: {f_pct:.0f}%. Overall level: {level}.",
        "detail_cn": f"A级：{a_pct:.0f}%，F级：{f_pct:.0f}%。整体水平：{level}。",
    })
    if avg_score < 55:
        recommendations.append({
            "id": "R-Q01",
            "recommendation": "Overall quality is low. Review process parameters systematically.",
            "recommendation_cn": "整体质量偏低，建议系统性地审查工艺参数。",
        })


def _correlation_findings(experiments: List[dict], findings: List[dict]):
    corr = correlation_matrix(experiments)
    sig = corr.get("significant_correlations", [])
    if not sig:
        findings.append({
            "id": "F-C01",
            "domain": "Correlation / 相关性",
            "finding": "No strong correlations detected between parameters with current sample size.",
            "finding_cn": "在当前样本量下未检测到参数间的强相关性。",
        })
        return
    top = sig[:3]
    for i, s in enumerate(top):
        findings.append({
            "id": f"F-C{i+1:02d}",
            "domain": "Correlation / 相关性",
            "finding": f"{s['param1']} vs {s['param2']}: r = {s['correlation']} ({s['strength']} {s['direction']}).",
            "finding_cn": f"{s['param1']} 与 {s['param2']}：r = {s['correlation']}（{s['strength_cn']}{s['direction']}）。",
        })


def _environment_findings(experiments: List[dict], findings: List[dict], recommendations: List[dict]):
    env_comparison = compare_groups(experiments, "environment")
    groups = env_comparison.get("groups", [])
    if len(groups) < 2:
        return
    # Find best and worst environments
    with_life = [g for g in groups if g["avg_service_life"] is not None]
    with_score = [g for g in groups if g["avg_quality"] is not None]
    if with_life:
        best_env = max(with_life, key=lambda g: g["avg_service_life"])
        worst_env = min(with_life, key=lambda g: g["avg_service_life"])
        findings.append({
            "id": "F-E01",
            "domain": "Environment / 环境",
            "finding": f"Best service life: {best_env['group']} ({best_env['avg_service_life']:.1f} yr avg). "
                       f"Worst: {worst_env['group']} ({worst_env['avg_service_life']:.1f} yr avg).",
            "finding_cn": f"最佳服役寿命：{best_env['group']}（平均{best_env['avg_service_life']:.1f}年）。"
                          f"最差：{worst_env['group']}（平均{worst_env['avg_service_life']:.1f}年）。",
        })
    if with_score:
        best_score = max(with_score, key=lambda g: g["avg_quality"])
        if best_score["avg_quality"] < 55:
            corrosive = [g for g in groups if g["group"] in
                         ("coastal", "underwater", "deep_sea", "corrosive_chemical")]
            if corrosive:
                recommendations.append({
                    "id": "R-E01",
                    "recommendation": "Corrosive/harsh environments show low scores. Consider material upgrade or coating solutions.",
                    "recommendation_cn": "腐蚀性/恶劣环境得分偏低，建议考虑材料升级或涂层方案。",
                })


def _process_findings(experiments: List[dict], findings: List[dict], recommendations: List[dict]):
    proc_comparison = compare_groups(experiments, "process")
    groups = proc_comparison.get("groups", [])
    if len(groups) < 2:
        return
    with_score = [g for g in groups if g["avg_quality"] is not None and g["count"] >= 2]
    if not with_score:
        return
    best = max(with_score, key=lambda g: g["avg_quality"])
    findings.append({
        "id": "F-P01",
        "domain": "Process / 工艺",
        "finding": f"Best process: {best['group']} (avg quality {best['avg_quality']:.1f}, {best['count']} experiments).",
        "finding_cn": f"最佳工艺：{best['group']}（平均质量{best['avg_quality']:.1f}，{best['count']}次实验）。",
    })
    low = [g for g in groups if g["avg_quality"] and g["avg_quality"] < 60 and g["count"] >= 2]
    for g in low:
        recommendations.append({
            "id": f"R-P-{g['group']}",
            "recommendation": f"Process '{g['group']}' consistently underperforms. Consider optimization or substitution.",
            "recommendation_cn": f"工艺'{g['group']}'表现持续不佳，建议优化或替换。",
        })


def _trend_outlier_findings(experiments: List[dict], findings: List[dict], recommendations: List[dict]):
    trend = trend_analysis(experiments)
    if "trend" in trend:
        findings.append({
            "id": "F-T01",
            "domain": "Trend / 趋势",
            "finding": f"Quality trend: {trend['trend']}. Correlation with sequence r={trend.get('correlation_with_sequence', 0)}.",
            "finding_cn": f"质量趋势：{trend['trend_cn']}（序列相关性 r={trend.get('correlation_with_sequence', 0)}）。",
        })
        if "Declining" in trend["trend"]:
            recommendations.append({
                "id": "R-T01",
                "recommendation": "Quality is declining over time. Investigate process drift, equipment wear, or material batch variation.",
                "recommendation_cn": "质量随时间下降，建议排查工艺漂移、设备磨损或材料批次差异。",
            })
    outliers = outlier_detection(experiments)
    outs = outliers.get("outliers", [])
    if outs:
        findings.append({
            "id": "F-O01",
            "domain": "Anomaly / 异常",
            "finding": f"Detected {len(outs)} outlier experiment(s) using IQR method.",
            "finding_cn": f"通过IQR方法检测到{len(outs)}个异常实验。",
            "detail": "; ".join(f"#{o['id']}: score={o['quality_score']}" for o in outs[:5]),
            "detail_cn": "；".join(f"#{o['id']}：分数={o['quality_score']}（{o['type']}）" for o in outs[:5]),
        })


def _material_findings(experiments: List[dict], findings: List[dict], recommendations: List[dict]):
    mat_comparison = compare_groups(experiments, "base_material")
    groups = mat_comparison.get("groups", [])
    if len(groups) < 2:
        return
    with_score = [g for g in groups if g["avg_quality"] is not None and g["count"] >= 2]
    if with_score:
        best_mat = max(with_score, key=lambda g: g["avg_quality"])
        worst_mat = min(with_score, key=lambda g: g["avg_quality"])
        findings.append({
            "id": "F-M01",
            "domain": "Material / 材料",
            "finding": f"Best material: {best_mat['group']} (avg score {best_mat['avg_quality']:.1f}). "
                       f"Most challenging: {worst_mat['group']} (avg score {worst_mat['avg_quality']:.1f}).",
            "finding_cn": f"最佳材料：{best_mat['group']}（平均{best_mat['avg_quality']:.1f}分）。"
                          f"最具挑战：{worst_mat['group']}（平均{worst_mat['avg_quality']:.1f}分）。",
        })


def _generate_summary(findings: List[dict], recommendations: List[dict],
                      experiments: List[dict]) -> dict:
    """Generate an executive summary from all findings."""
    n = len(experiments)
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    # Key takeaways
    quality_findings = [f for f in findings if "Quality" in f.get("domain", "")]
    env_findings = [f for f in findings if "Environment" in f.get("domain", "")]
    trend_findings = [f for f in findings if "Trend" in f.get("domain", "")]
    lines_en = [
        f"=== Research Conclusions / 研究结论 ===",
        f"Analysis Date: {now}",
        f"Experiments Analyzed: {n}",
        f"Key Findings: {len(findings)}",
        f"Research Recommendations: {len(recommendations)}",
        "",
        "--- Key Findings ---",
    ]
    lines_cn = [
        f"=== 研究结论 / Research Conclusions ===",
        f"分析日期：{now}",
        f"分析实验数：{n}",
        f"关键发现：{len(findings)}",
        f"研究建议：{len(recommendations)}",
        "",
        "--- 关键发现 ---",
    ]
    for f in findings:
        lines_en.append(f"  [{f['domain']}] {f['finding']}")
        lines_cn.append(f"  [{f['domain']}] {f['finding_cn']}")
    if recommendations:
        lines_en.append("")
        lines_en.append("--- Recommendations ---")
        lines_cn.append("")
        lines_cn.append("--- 研究建议 ---")
        for r in recommendations:
            lines_en.append(f"  * {r['recommendation']}")
            lines_cn.append(f"  * {r['recommendation_cn']}")
    return {
        "en": "\n".join(lines_en),
        "cn": "\n".join(lines_cn),
    }
