"""
Experiment database: SQLite-backed storage for research experiments.
实验数据库：基于SQLite的研究实验数据存储。
CRUD operations, search, filter, batch import, export.
"""
import sqlite3
import json
import os
import csv
import io
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "outputs")
DB_PATH = os.path.join(DB_DIR, "experiments.db")


def _get_conn() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize experiment database tables.
    初始化实验数据库表。"""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            exp_name TEXT NOT NULL,
            exp_date TEXT DEFAULT (date('now')),
            operator TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            base_material TEXT NOT NULL,
            filler_material TEXT DEFAULT '',
            process TEXT DEFAULT 'GTAW',
            current_A REAL DEFAULT 150,
            voltage_V REAL DEFAULT 20,
            travel_speed_mm_s REAL DEFAULT 2.0,
            arc_efficiency REAL DEFAULT 0.75,
            electrode_diameter_mm REAL DEFAULT 2.4,
            torch_angle_deg REAL DEFAULT 90,
            polarity TEXT DEFAULT 'DCEN',
            preheat_temp_C REAL DEFAULT 25,
            interpass_temp_C REAL DEFAULT 150,
            joint_type TEXT DEFAULT 'butt',
            weld_position TEXT DEFAULT '1G',
            plate_thickness_mm REAL DEFAULT 10,
            bevel_angle_deg REAL DEFAULT 30,
            groove_type TEXT DEFAULT 'V',
            number_of_passes INTEGER DEFAULT 3,
            environment TEXT DEFAULT 'indoor_standard',
            quality_score REAL,
            quality_grade TEXT,
            overall_risk TEXT,
            heat_input_kJ_mm REAL,
            t8_5_s REAL,
            haz_width_mm REAL,
            residual_stress_MPa REAL,
            predicted_yield_MPa REAL,
            corrosion_rate_mm_yr REAL,
            service_life_years REAL,
            analysis_json TEXT DEFAULT '{}',
            tags TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_exp_project ON experiments(project_id);
        CREATE INDEX IF NOT EXISTS idx_exp_date ON experiments(exp_date);
        CREATE INDEX IF NOT EXISTS idx_exp_material ON experiments(base_material);
        CREATE INDEX IF NOT EXISTS idx_exp_grade ON experiments(quality_grade);
    """)
    conn.commit()
    conn.close()


# ---- Projects CRUD / 项目管理 ----

def create_project(name: str, description: str = "") -> dict:
    conn = _get_conn()
    cur = conn.execute("INSERT INTO projects (name, description) VALUES (?, ?)", (name, description))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return {"id": pid, "name": name, "description": description}


def list_projects() -> List[dict]:
    conn = _get_conn()
    rows = conn.execute("""
        SELECT p.*, COUNT(e.id) as exp_count
        FROM projects p LEFT JOIN experiments e ON p.id = e.project_id
        GROUP BY p.id ORDER BY p.updated_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_project(project_id: int) -> bool:
    conn = _get_conn()
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    return True


# ---- Experiments CRUD / 实验数据管理 ----

def add_experiment(data: dict) -> dict:
    """Add a single experiment record.
    添加单条实验记录。"""
    conn = _get_conn()
    fields = [
        "project_id", "exp_name", "exp_date", "operator", "notes",
        "base_material", "filler_material", "process", "current_A", "voltage_V",
        "travel_speed_mm_s", "arc_efficiency", "electrode_diameter_mm",
        "torch_angle_deg", "polarity", "preheat_temp_C", "interpass_temp_C",
        "joint_type", "weld_position", "plate_thickness_mm", "bevel_angle_deg",
        "groove_type", "number_of_passes", "environment",
        "quality_score", "quality_grade", "overall_risk",
        "heat_input_kJ_mm", "t8_5_s", "haz_width_mm",
        "residual_stress_MPa", "predicted_yield_MPa",
        "corrosion_rate_mm_yr", "service_life_years",
        "analysis_json", "tags",
    ]
    values = []
    placeholders = []
    for f in fields:
        val = data.get(f)
        if isinstance(val, (dict, list)):
            val = json.dumps(val, ensure_ascii=False)
        values.append(val)
        placeholders.append("?")
    sql = f"INSERT INTO experiments ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
    cur = conn.execute(sql, values)
    conn.commit()
    eid = cur.lastrowid
    # Update project timestamp
    if data.get("project_id"):
        conn.execute("UPDATE projects SET updated_at=datetime('now') WHERE id=?", (data["project_id"],))
        conn.commit()
    conn.close()
    return {"id": eid, "exp_name": data.get("exp_name", "")}


def batch_add_experiments(records: List[dict]) -> dict:
    """Batch add experiments from list of dicts.
    批量添加实验记录。"""
    added = 0
    errors = []
    for i, rec in enumerate(records):
        try:
            add_experiment(rec)
            added += 1
        except Exception as e:
            errors.append({"index": i, "error": str(e)})
    return {"added": added, "errors": errors, "total": len(records)}


def import_csv(csv_data: str, project_id: Optional[int] = None) -> dict:
    """Import experiments from CSV string.
    从CSV字符串导入实验数据。"""
    reader = csv.DictReader(io.StringIO(csv_data))
    records = []
    for row in reader:
        rec = {}
        # Map CSV columns to DB fields
        mapping = {
            "exp_name": ["exp_name", "name", "experiment", "实验名称"],
            "base_material": ["base_material", "material", "base", "母材"],
            "process": ["process", "weld_process", "工艺"],
            "current_A": ["current", "current_A", "电流"],
            "voltage_V": ["voltage", "voltage_V", "电压"],
            "travel_speed_mm_s": ["travel_speed", "speed", "速度"],
            "preheat_temp_C": ["preheat_temp", "preheat", "预热温度"],
            "plate_thickness_mm": ["plate_thickness", "thickness", "板厚"],
            "environment": ["environment", "env", "环境"],
            "quality_score": ["quality_score", "score", "质量分数"],
            "quality_grade": ["quality_grade", "grade", "质量等级"],
            "notes": ["notes", "备注", "note"],
        }
        for db_field, csv_cols in mapping.items():
            for col in csv_cols:
                if col in row and row[col].strip():
                    val = row[col].strip()
                    if db_field in ("current_A", "voltage_V", "travel_speed_mm_s",
                                     "preheat_temp_C", "plate_thickness_mm", "quality_score"):
                        try:
                            val = float(val)
                        except ValueError:
                            pass
                    rec[db_field] = val
                    break
        if project_id:
            rec["project_id"] = project_id
        if not rec.get("exp_name"):
            rec["exp_name"] = f"CSV-Import-{len(records)+1}"
        records.append(rec)
    return batch_add_experiments(records)


def get_experiment(exp_id: int) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d.get("analysis_json"):
            try:
                d["analysis"] = json.loads(d["analysis_json"])
            except json.JSONDecodeError:
                d["analysis"] = {}
        return d
    return None


def list_experiments(project_id: Optional[int] = None, limit: int = 100,
                     offset: int = 0, search: str = "",
                     sort_by: str = "created_at", sort_order: str = "DESC",
                     grade_filter: str = "") -> dict:
    """List experiments with filtering and pagination.
    带筛选和分页的实验列表。"""
    conn = _get_conn()
    where_clauses = []
    params = []
    if project_id is not None:
        where_clauses.append("e.project_id = ?")
        params.append(project_id)
    if search:
        where_clauses.append("(e.exp_name LIKE ? OR e.base_material LIKE ? OR e.notes LIKE ? OR e.tags LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like, like])
    if grade_filter:
        where_clauses.append("e.quality_grade = ?")
        params.append(grade_filter)
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    valid_sort = {"created_at", "exp_date", "quality_score", "base_material", "exp_name"}
    if sort_by not in valid_sort:
        sort_by = "created_at"
    sort_order = "DESC" if sort_order.upper() == "DESC" else "ASC"
    # Count
    count_row = conn.execute(f"SELECT COUNT(*) as cnt FROM experiments e {where_sql}", params).fetchone()
    total = count_row["cnt"]
    # Fetch
    rows = conn.execute(
        f"SELECT e.*, p.name as project_name FROM experiments e "
        f"LEFT JOIN projects p ON e.project_id = p.id "
        f"{where_sql} ORDER BY e.{sort_by} {sort_order} LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()
    conn.close()
    return {
        "experiments": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def update_experiment(exp_id: int, data: dict) -> bool:
    conn = _get_conn()
    allowed_fields = {
        "exp_name", "notes", "operator", "exp_date", "project_id",
        "quality_score", "quality_grade", "overall_risk",
        "heat_input_kJ_mm", "t8_5_s", "haz_width_mm",
        "residual_stress_MPa", "predicted_yield_MPa",
        "corrosion_rate_mm_yr", "service_life_years",
        "analysis_json", "tags",
    }
    updates = {}
    for k, v in data.items():
        if k in allowed_fields:
            if isinstance(v, (dict, list)):
                v = json.dumps(v, ensure_ascii=False)
            updates[k] = v
    if not updates:
        conn.close()
        return False
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [exp_id]
    conn.execute(f"UPDATE experiments SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


def delete_experiment(exp_id: int) -> bool:
    conn = _get_conn()
    conn.execute("DELETE FROM experiments WHERE id = ?", (exp_id,))
    conn.commit()
    conn.close()
    return True


def get_statistics(project_id: Optional[int] = None) -> dict:
    """Get aggregate statistics for experiments.
    获取实验汇总统计。"""
    conn = _get_conn()
    where = "WHERE project_id = ?" if project_id else "WHERE 1=1"
    params = [project_id] if project_id else [1]
    stats = {}
    # Grade distribution
    rows = conn.execute(
        f"SELECT quality_grade, COUNT(*) as cnt FROM experiments {where} AND quality_grade IS NOT NULL "
        f"GROUP BY quality_grade", params
    ).fetchall()
    stats["grade_distribution"] = {r["quality_grade"]: r["cnt"] for r in rows}
    # Material distribution
    rows = conn.execute(
        f"SELECT base_material, COUNT(*) as cnt FROM experiments {where} "
        f"GROUP BY base_material ORDER BY cnt DESC LIMIT 10", params
    ).fetchall()
    stats["top_materials"] = [{"material": r["base_material"], "count": r["cnt"]} for r in rows]
    # Environment distribution
    rows = conn.execute(
        f"SELECT environment, COUNT(*) as cnt FROM experiments {where} "
        f"GROUP BY environment ORDER BY cnt DESC", params
    ).fetchall()
    stats["top_environments"] = [{"environment": r["environment"], "count": r["cnt"]} for r in rows]
    # Aggregate quality
    row = conn.execute(
        f"SELECT AVG(quality_score) as avg_score, MAX(quality_score) as max_score, "
        f"MIN(quality_score) as min_score, COUNT(*) as total "
        f"FROM experiments {where} AND quality_score IS NOT NULL", params
    ).fetchone()
    if row:
        stats["quality"] = {
            "avg_score": round(row["avg_score"], 1) if row["avg_score"] else None,
            "max_score": row["max_score"],
            "min_score": row["min_score"],
            "total_rated": row["total"],
        }
    # Aggregate physics
    for field, label in [("haz_width_mm", "avg_haz_width"),
                          ("residual_stress_MPa", "avg_residual_stress"),
                          ("service_life_years", "avg_service_life"),
                          ("corrosion_rate_mm_yr", "avg_corrosion_rate")]:
        row = conn.execute(
            f"SELECT AVG({field}) as val FROM experiments {where} AND {field} IS NOT NULL", params
        ).fetchone()
        stats[label] = round(row["val"], 2) if row and row["val"] else None
    conn.close()
    return stats


def export_experiments_csv(project_id: Optional[int] = None) -> str:
    """Export experiments as CSV string.
    导出实验数据为CSV字符串。"""
    conn = _get_conn()
    where = "WHERE project_id = ?" if project_id else ""
    params = [project_id] if project_id else []
    rows = conn.execute(
        f"SELECT * FROM experiments {where} ORDER BY created_at DESC", params
    ).fetchall()
    conn.close()
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.writer(output)
    # Header
    headers = [k for k in rows[0].keys() if k != "analysis_json"]
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row[k] for k in headers])
    return output.getvalue()


# Initialize DB on import
init_db()
