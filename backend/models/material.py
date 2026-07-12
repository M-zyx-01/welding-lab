"""Material analysis: carbon equivalent, weldability, filler compatibility."""
import math
from ..data.weld_data import MaterialSpec

def carbon_equivalent(mat: MaterialSpec) -> float:
    comp = mat.composition
    ce = (comp.get("C",0.0) + comp.get("Mn",0.0)/6.0 +
          (comp.get("Cr",0.0)+comp.get("Mo",0.0)+comp.get("V",0.0))/5.0 +
          (comp.get("Ni",0.0)+comp.get("Cu",0.0))/15.0)
    return round(ce, 4)

def pcm_value(mat: MaterialSpec) -> float:
    comp = mat.composition
    pcm = (comp.get("C",0.0)+comp.get("Si",0.0)/30.0+
           (comp.get("Mn",0.0)+comp.get("Cu",0.0))/20.0+
           comp.get("Ni",0.0)/60.0+comp.get("Cr",0.0)/20.0+
           comp.get("Mo",0.0)/15.0+comp.get("V",0.0)/10.0+
           5.0*comp.get("B",0.0))
    return round(pcm, 4)

def weldability_assessment(mat: MaterialSpec) -> dict:
    ce = carbon_equivalent(mat)
    pcm = pcm_value(mat)
    if ce < 0.35:
        ce_risk, ce_note = "Low", "??<25mm???????????"
    elif ce < 0.45:
        ce_risk, ce_note = "Moderate", "????100-200 C???????"
    elif ce < 0.60:
        ce_risk, ce_note = "High", "????200-350 C????????"
    else:
        ce_risk, ce_note = "Very High", "??????????????????"
    is_aluminium = mat.density < 5000
    is_stainless = mat.composition.get("Cr",0) > 10
    is_titanium = mat.composition.get("Ti",0) > 50
    recommendations = []
    if is_aluminium:
        recommendations += ["Use AC-GTAW or DCEP-GMAW for oxide cleaning",
                           "Remove oxide layer immediately before welding",
                           "Preheat to 100-150 C for sections > 10 mm"]
    if is_stainless:
        recommendations += ["Control interpass temperature < 150 C",
                           "Use low heat input (typically < 1.5 kJ/mm)",
                           "Back-purge with argon for full-penetration welds"]
    if is_titanium:
        recommendations += ["Trailing shield required; O2 < 50 ppm in purge",
                           "Colour check: silver/straw = ok; blue/grey = reject"]
    if mat.youngs_modulus > 190e9 and not is_stainless:
        recommendations.append("Consider PWHT at 600-650 C for stress relief")
    if mat.density < 5000: preheat = 120.0
    elif is_titanium: preheat = 25.0
    elif ce < 0.35: preheat = 20.0
    elif ce < 0.45: preheat = 150.0
    elif ce < 0.60: preheat = 250.0
    else: preheat = 350.0
    return {"carbon_equivalent":ce, "pcm":pcm, "cracking_risk":ce_risk,
            "ce_note":ce_note, "recommendations":recommendations,
            "suggested_preheat_C":preheat,
            "suggested_interpass_max_C":150 if is_stainless else 300}

def filler_compatibility(base: MaterialSpec, filler: MaterialSpec) -> dict:
    results = {"strength_match":"Undermatching","cte_match":"Acceptable",
               "galvanic_risk":"Low","overall":"Caution","notes":[]}
    ratio = filler.yield_strength/base.yield_strength if base.yield_strength>0 else 0
    if 0.95<=ratio<=1.20: results["strength_match"]="Matching"
    elif ratio>1.20: results["strength_match"]="Overmatching"
    if ratio<0.85: results["notes"].append("?????????????????????")
    elif ratio>1.30: results["notes"].append("??????????????????")
    cte_diff = abs(filler.cte-base.cte)/base.cte if base.cte>0 else 0
    if cte_diff>0.30:
        results["cte_match"]="High Mismatch"
        results["notes"].append(f"???????? ({cte_diff*100:.1f}%): ??????????")
    elif cte_diff>0.15: results["cte_match"]="Moderate Mismatch"
    if base.density>7000 and filler.density<5000:
        results["galvanic_risk"]="High (dissimilar metals)"
        results["notes"].append("Galvanic corrosion risk: isolate joint or use transition piece")
    elif base.density>7000 and filler.composition.get("Cr",0)>10:
        results["galvanic_risk"]="Low-Moderate"
    risk_count=sum([results["strength_match"]=="Undermatching",
                    results["cte_match"]in("High Mismatch","Moderate Mismatch"),
                    results["galvanic_risk"].startswith("High")])
    if risk_count==0: results["overall"]="Good"
    elif risk_count==1: results["overall"]="Acceptable"
    return results
