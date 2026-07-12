"""Welding Lab - CLI Analysis Tool
Usage: python welding-lab/run_analysis.py [--material Q345] [--process GTAW] [--env coastal]
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.data.weld_data import (
    WeldInput, MaterialSpec, WeldParameters, WeldJoint,
    WeldProcess, JointType, WeldPosition, Environment,
)
from backend.data.material_db import get_material, list_materials
from backend.analysis.predictor import run_full_analysis, predict_weld_quality
from backend.analysis.report import generate_report

def main():
    parser = argparse.ArgumentParser(description="Welding Lab - Multi-Physics Analysis CLI")
    parser.add_argument("--material", default="Q345", help="Base material key")
    parser.add_argument("--filler", default=None, help="Filler material key (optional)")
    parser.add_argument("--process", default="GTAW", choices=[p.value for p in WeldProcess])
    parser.add_argument("--current", type=float, default=150, help="Current (A)")
    parser.add_argument("--voltage", type=float, default=20, help="Voltage (V)")
    parser.add_argument("--speed", type=float, default=2.0, help="Travel speed (mm/s)")
    parser.add_argument("--efficiency", type=float, default=0.70, help="Arc efficiency")
    parser.add_argument("--thickness", type=float, default=10, help="Plate thickness (mm)")
    parser.add_argument("--joint", default="butt", choices=["butt","lap","tee","corner","edge"])
    parser.add_argument("--env", default="indoor_standard", choices=[e.value for e in Environment])
    parser.add_argument("--preheat", type=float, default=25, help="Preheat temp (C)")
    parser.add_argument("--polarity", default="DCEN", choices=["DCEN","DCEP","AC"])
    parser.add_argument("--electrode", type=float, default=2.4, help="Electrode dia (mm)")
    parser.add_argument("--report", action="store_true", help="Generate full markdown report")
    parser.add_argument("--list-materials", action="store_true", help="List available materials")
    parser.add_argument("--output", default=None, help="Output JSON file path")

    args = parser.parse_args()

    if args.list_materials:
        print("Available materials:")
        for k in list_materials():
            m = get_material(k)
            print(f"  {k}: {m.name} (Yield: {m.yield_strength/1e6:.0f} MPa)")
        return

    mat = get_material(args.material)
    filler = get_material(args.filler) if args.filler else None

    params = WeldParameters(
        process=WeldProcess(args.process),
        current=args.current, voltage=args.voltage, travel_speed=args.speed,
        arc_efficiency=args.efficiency, electrode_diameter=args.electrode,
        preheat_temp=args.preheat, polarity=args.polarity,
    )
    joint = WeldJoint(joint_type=JointType(args.joint), plate_thickness=args.thickness)
    env = Environment(args.env)

    weld = WeldInput(
        id=f"cli-{args.material}-{args.process}",
        base_material=mat, filler_material=filler,
        parameters=params, joint=joint, environment=env,
    )

    if args.report:
        report = generate_report(weld)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)
    else:
        analysis = run_full_analysis(weld)
        quality = predict_weld_quality(weld)
        result = {"analysis": analysis, "quality": quality}
        if args.output:
            result_serializable = json.loads(json.dumps(result, default=str))
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result_serializable, f, ensure_ascii=False, indent=2)
            print(f"Analysis saved to {args.output}")
        else:
            print(json.dumps({"quality": quality, "summary": analysis["summary"]}, ensure_ascii=False, indent=2, default=str))

if __name__ == "__main__":
    main()
