from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "fp_data.db"

PROCESS_CATEGORIES = {
    "Litografia": ["Optica", "Feixe de eletrons"],
    "Deposicao": ["Sputtering", "Evaporacao"],
    "Ataque": ["Umido", "RIE", "DRIE", "Ion Milling"],
    "Inspecao": ["MEV", "TEM", "Microscopio optico", "Probe Station"],
    "Preparacao": ["FIB", "Wire Bonder"],
}

EQUIPMENT_STATUSES = {"active", "inactive"}
RECIPE_STATUSES = {"experimental", "provisoria", "validada", "rotina", "obsoleta"}
SHEET_STATUSES = {"draft", "review", "approved", "obsolete"}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                subtype TEXT NOT NULL,
                model TEXT,
                manufacturer TEXT,
                location TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS recipe_block (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                subtype TEXT NOT NULL,
                equipment_id INTEGER NOT NULL,
                author TEXT,
                confidence_level TEXT NOT NULL DEFAULT 'experimental',
                description TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(equipment_id) REFERENCES equipment(id)
            );

            CREATE TABLE IF NOT EXISTS recipe_parameter (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_block_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                value TEXT,
                unit TEXT,
                seq INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(recipe_block_id) REFERENCES recipe_block(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS process_sheet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                project_name TEXT,
                supervisor TEXT,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS process_sheet_block (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_sheet_id INTEGER NOT NULL,
                recipe_block_id INTEGER NOT NULL,
                seq INTEGER NOT NULL,
                title_override TEXT,
                notes_override TEXT,
                FOREIGN KEY(process_sheet_id) REFERENCES process_sheet(id) ON DELETE CASCADE,
                FOREIGN KEY(recipe_block_id) REFERENCES recipe_block(id)
            );

            CREATE TABLE IF NOT EXISTS generated_sheet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_sheet_id INTEGER,
                output_path TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(process_sheet_id) REFERENCES process_sheet(id)
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                action TEXT NOT NULL,
                payload TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS recipe_block_revision (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_block_id INTEGER NOT NULL,
                revision_no INTEGER NOT NULL,
                action TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS process_sheet_revision (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_sheet_id INTEGER NOT NULL,
                revision_no INTEGER NOT NULL,
                action TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_recipe_block_category ON recipe_block(category, subtype);
            CREATE INDEX IF NOT EXISTS idx_sheet_block_sheet ON process_sheet_block(process_sheet_id, seq);
            """
        )
        _migrate_equipment_columns(conn)
        _migrate_generated_sheet_columns(conn)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_equipment_category ON equipment(category, subtype, status)")


def _migrate_equipment_columns(conn: sqlite3.Connection) -> None:
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(equipment)").fetchall()}
    migrations = {
        "subtype": "ALTER TABLE equipment ADD COLUMN subtype TEXT NOT NULL DEFAULT 'Geral'",
        "location": "ALTER TABLE equipment ADD COLUMN location TEXT",
        "status": "ALTER TABLE equipment ADD COLUMN status TEXT NOT NULL DEFAULT 'active'",
        "updated_at": "ALTER TABLE equipment ADD COLUMN updated_at TEXT",
    }
    for col, sql in migrations.items():
        if col not in cols:
            conn.execute(sql)
    if "category" not in cols:
        conn.execute("ALTER TABLE equipment ADD COLUMN category TEXT NOT NULL DEFAULT 'Preparacao'")
    if "manufacturer" not in cols:
        conn.execute("ALTER TABLE equipment ADD COLUMN manufacturer TEXT")
    if "model" not in cols:
        conn.execute("ALTER TABLE equipment ADD COLUMN model TEXT")
    if "notes" not in cols:
        conn.execute("ALTER TABLE equipment ADD COLUMN notes TEXT")


def _migrate_generated_sheet_columns(conn: sqlite3.Connection) -> None:
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(generated_sheet)").fetchall()}
    if "process_sheet_id" not in cols:
        conn.execute("ALTER TABLE generated_sheet ADD COLUMN process_sheet_id INTEGER")


def list_categories() -> dict[str, list[str]]:
    return PROCESS_CATEGORIES


def _normalize_status(value: str, allowed: set[str], default: str) -> str:
    status = (value or default).strip().lower()
    return status if status in allowed else default


def log_audit(conn: sqlite3.Connection, entity_type: str, entity_id: int | None, action: str, payload: dict[str, Any] | None = None) -> None:
    conn.execute(
        "INSERT INTO audit_log(entity_type, entity_id, action, payload) VALUES(?, ?, ?, ?)",
        (entity_type, entity_id, action, json.dumps(payload, ensure_ascii=False) if payload is not None else None),
    )


def list_audit_log(limit: int = 100) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, entity_type, entity_id, action, payload, created_at
            FROM audit_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return _rows_to_dicts(rows)


def _next_revision_no(conn: sqlite3.Connection, table: str, entity_column: str, entity_id: int) -> int:
    row = conn.execute(
        f"SELECT COALESCE(MAX(revision_no), 0) + 1 AS next_no FROM {table} WHERE {entity_column} = ?",
        (entity_id,),
    ).fetchone()
    return int(row["next_no"])


def log_recipe_block_revision(
    conn: sqlite3.Connection, recipe_block_id: int, action: str, payload: dict[str, Any]
) -> None:
    conn.execute(
        """
        INSERT INTO recipe_block_revision(recipe_block_id, revision_no, action, payload)
        VALUES(?, ?, ?, ?)
        """,
        (recipe_block_id, _next_revision_no(conn, "recipe_block_revision", "recipe_block_id", recipe_block_id), action, json.dumps(payload, ensure_ascii=False)),
    )


def log_process_sheet_revision(
    conn: sqlite3.Connection, process_sheet_id: int, action: str, payload: dict[str, Any]
) -> None:
    conn.execute(
        """
        INSERT INTO process_sheet_revision(process_sheet_id, revision_no, action, payload)
        VALUES(?, ?, ?, ?)
        """,
        (process_sheet_id, _next_revision_no(conn, "process_sheet_revision", "process_sheet_id", process_sheet_id), action, json.dumps(payload, ensure_ascii=False)),
    )


def list_recipe_block_revisions(recipe_block_id: int) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, recipe_block_id, revision_no, action, payload, created_at
            FROM recipe_block_revision
            WHERE recipe_block_id = ?
            ORDER BY revision_no DESC, id DESC
            """,
            (recipe_block_id,),
        ).fetchall()
    return _rows_to_dicts(rows)


def list_process_sheet_revisions(process_sheet_id: int) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, process_sheet_id, revision_no, action, payload, created_at
            FROM process_sheet_revision
            WHERE process_sheet_id = ?
            ORDER BY revision_no DESC, id DESC
            """,
            (process_sheet_id,),
        ).fetchall()
    return _rows_to_dicts(rows)


def list_equipment(include_inactive: bool = False) -> list[dict[str, Any]]:
    where = "" if include_inactive else "WHERE status = 'active'"
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT id, name, category, subtype, model, manufacturer, location, status, notes, created_at, updated_at
            FROM equipment
            {where}
            ORDER BY category, subtype, name, id
            """
        ).fetchall()
    return _rows_to_dicts(rows)


def get_equipment(equipment_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, name, category, subtype, model, manufacturer, location, status, notes, created_at, updated_at
            FROM equipment
            WHERE id = ?
            """,
            (equipment_id,),
        ).fetchone()
    return _row_to_dict(row)


def create_equipment(data: dict[str, Any]) -> dict[str, Any]:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO equipment(name, category, subtype, model, manufacturer, location, status, notes)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"].strip(),
                data["category"].strip(),
                data["subtype"].strip(),
                data.get("model", "").strip(),
                data.get("manufacturer", "").strip(),
                data.get("location", "").strip(),
                _normalize_status(data.get("status", "active"), EQUIPMENT_STATUSES, "active"),
                data.get("notes", "").strip(),
            ),
        )
        equipment_id = cur.lastrowid
        log_audit(conn, "equipment", equipment_id, "create", get_equipment(equipment_id))
    return get_equipment(equipment_id) or {}


def update_equipment(equipment_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE equipment
            SET name = ?, category = ?, subtype = ?, model = ?, manufacturer = ?,
                location = ?, status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                data["name"].strip(),
                data["category"].strip(),
                data["subtype"].strip(),
                data.get("model", "").strip(),
                data.get("manufacturer", "").strip(),
                data.get("location", "").strip(),
                _normalize_status(data.get("status", "active"), EQUIPMENT_STATUSES, "active"),
                data.get("notes", "").strip(),
                equipment_id,
            ),
        )
        log_audit(conn, "equipment", equipment_id, "update", get_equipment(equipment_id))
    return get_equipment(equipment_id)


def delete_equipment(equipment_id: int) -> bool:
    with get_conn() as conn:
        used = conn.execute(
            "SELECT COUNT(*) AS total FROM recipe_block WHERE equipment_id = ?",
            (equipment_id,),
        ).fetchone()["total"]
        if used:
            conn.execute(
                "UPDATE equipment SET status = 'inactive', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (equipment_id,),
            )
            return False
        conn.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))
        log_audit(conn, "equipment", equipment_id, "delete", {"removed": True})
    return True


def list_recipe_blocks() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT rb.id, rb.name, rb.category, rb.subtype, rb.equipment_id, rb.author,
                   rb.confidence_level, rb.description, rb.notes, rb.created_at, rb.updated_at,
                   e.name AS equipment_name, e.model AS equipment_model
            FROM recipe_block rb
            JOIN equipment e ON e.id = rb.equipment_id
            ORDER BY rb.category, rb.subtype, rb.name, rb.id
            """
        ).fetchall()
    blocks = _rows_to_dicts(rows)
    for block in blocks:
        block["parameters"] = list_recipe_parameters(block["id"])
    return blocks


def get_recipe_block(recipe_block_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT rb.id, rb.name, rb.category, rb.subtype, rb.equipment_id, rb.author,
                   rb.confidence_level, rb.description, rb.notes, rb.created_at, rb.updated_at,
                   e.name AS equipment_name, e.model AS equipment_model
            FROM recipe_block rb
            JOIN equipment e ON e.id = rb.equipment_id
            WHERE rb.id = ?
            """,
            (recipe_block_id,),
        ).fetchone()
    block = _row_to_dict(row)
    if block:
        block["parameters"] = list_recipe_parameters(recipe_block_id)
    return block


def list_recipe_parameters(recipe_block_id: int) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, recipe_block_id, name, value, unit, seq
            FROM recipe_parameter
            WHERE recipe_block_id = ?
            ORDER BY seq, id
            """,
            (recipe_block_id,),
        ).fetchall()
    return _rows_to_dicts(rows)


def create_recipe_block(data: dict[str, Any]) -> dict[str, Any]:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO recipe_block(
                name, category, subtype, equipment_id, author, confidence_level, description, notes
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"].strip(),
                data["category"].strip(),
                data["subtype"].strip(),
                int(data["equipment_id"]),
                data.get("author", "").strip(),
                _normalize_status(data.get("confidence_level", "experimental"), RECIPE_STATUSES, "experimental"),
                data.get("description", "").strip(),
                data.get("notes", "").strip(),
            ),
        )
        recipe_block_id = cur.lastrowid
        _replace_recipe_parameters(conn, recipe_block_id, data.get("parameters", []))
        snapshot = {
            "id": recipe_block_id,
            "name": data["name"].strip(),
            "category": data["category"].strip(),
            "subtype": data["subtype"].strip(),
            "equipment_id": int(data["equipment_id"]),
            "author": data.get("author", "").strip(),
            "confidence_level": _normalize_status(data.get("confidence_level", "experimental"), RECIPE_STATUSES, "experimental"),
            "description": data.get("description", "").strip(),
            "notes": data.get("notes", "").strip(),
            "parameters": data.get("parameters", []),
        }
        log_audit(conn, "recipe_block", recipe_block_id, "create", snapshot)
        log_recipe_block_revision(conn, recipe_block_id, "create", snapshot)
    return get_recipe_block(recipe_block_id) or {}


def update_recipe_block(recipe_block_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    with get_conn() as conn:
        approved_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM process_sheet_block psb
            JOIN process_sheet ps ON ps.id = psb.process_sheet_id
            WHERE psb.recipe_block_id = ? AND ps.status IN ('approved', 'obsolete')
            """,
            (recipe_block_id,),
        ).fetchone()["total"]
        if approved_count > 0:
            raise ValueError(
                "Este bloco de receita esta sendo usado por uma folha de processo aprovada ou obsoleta e nao pode ser modificado. Por favor, duplique o bloco para criar uma variacao."
            )
        conn.execute(
            """
            UPDATE recipe_block
            SET name = ?, category = ?, subtype = ?, equipment_id = ?, author = ?,
                confidence_level = ?, description = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                data["name"].strip(),
                data["category"].strip(),
                data["subtype"].strip(),
                int(data["equipment_id"]),
                data.get("author", "").strip(),
                _normalize_status(data.get("confidence_level", "experimental"), RECIPE_STATUSES, "experimental"),
                data.get("description", "").strip(),
                data.get("notes", "").strip(),
                recipe_block_id,
            ),
        )
        _replace_recipe_parameters(conn, recipe_block_id, data.get("parameters", []))
        snapshot = {
            "id": recipe_block_id,
            "name": data["name"].strip(),
            "category": data["category"].strip(),
            "subtype": data["subtype"].strip(),
            "equipment_id": int(data["equipment_id"]),
            "author": data.get("author", "").strip(),
            "confidence_level": _normalize_status(data.get("confidence_level", "experimental"), RECIPE_STATUSES, "experimental"),
            "description": data.get("description", "").strip(),
            "notes": data.get("notes", "").strip(),
            "parameters": data.get("parameters", []),
        }
        log_audit(conn, "recipe_block", recipe_block_id, "update", snapshot)
        log_recipe_block_revision(conn, recipe_block_id, "update", snapshot)
    return get_recipe_block(recipe_block_id)


def duplicate_recipe_block(recipe_block_id: int) -> dict[str, Any] | None:
    source = get_recipe_block(recipe_block_id)
    if not source:
        return None
    payload = {
        "name": f"{source['name']} - 1",
        "category": source["category"],
        "subtype": source["subtype"],
        "equipment_id": source["equipment_id"],
        "author": source.get("author") or "",
        "confidence_level": source.get("confidence_level") or "experimental",
        "description": source.get("description") or "",
        "notes": source.get("notes") or "",
        "parameters": [
            {
                "name": param.get("name") or "",
                "value": param.get("value") or "",
                "unit": param.get("unit") or "",
            }
            for param in source.get("parameters", [])
        ],
    }
    return create_recipe_block(payload)


def _replace_recipe_parameters(
    conn: sqlite3.Connection, recipe_block_id: int, parameters: list[dict[str, Any]]
) -> None:
    conn.execute("DELETE FROM recipe_parameter WHERE recipe_block_id = ?", (recipe_block_id,))
    for seq, param in enumerate(parameters, start=1):
        name = str(param.get("name", "")).strip()
        if not name:
            continue
        conn.execute(
            """
            INSERT INTO recipe_parameter(recipe_block_id, name, value, unit, seq)
            VALUES(?, ?, ?, ?, ?)
            """,
            (
                recipe_block_id,
                name,
                str(param.get("value", "")).strip(),
                str(param.get("unit", "")).strip(),
                seq,
            ),
        )


def delete_recipe_block(recipe_block_id: int) -> bool:
    with get_conn() as conn:
        used = conn.execute(
            "SELECT COUNT(*) AS total FROM process_sheet_block WHERE recipe_block_id = ?",
            (recipe_block_id,),
        ).fetchone()["total"]
        if used:
            return False
        current = get_recipe_block(recipe_block_id) or {"id": recipe_block_id}
        conn.execute("DELETE FROM recipe_block WHERE id = ?", (recipe_block_id,))
        log_audit(conn, "recipe_block", recipe_block_id, "delete", current)
        log_recipe_block_revision(conn, recipe_block_id, "delete", current)
    return True


def list_process_sheets() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, title, author, project_name, supervisor, description, status, created_at, updated_at
            FROM process_sheet
            ORDER BY id DESC
            """
        ).fetchall()
    sheets = _rows_to_dicts(rows)
    for sheet in sheets:
        sheet["blocks"] = list_process_sheet_blocks(sheet["id"])
    return sheets


def get_process_sheet(process_sheet_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, title, author, project_name, supervisor, description, status, created_at, updated_at
            FROM process_sheet
            WHERE id = ?
            """,
            (process_sheet_id,),
        ).fetchone()
    sheet = _row_to_dict(row)
    if sheet:
        sheet["blocks"] = list_process_sheet_blocks(process_sheet_id)
    return sheet


def list_process_sheet_blocks(process_sheet_id: int) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT psb.id, psb.process_sheet_id, psb.recipe_block_id, psb.seq,
                   psb.title_override, psb.notes_override,
                   rb.name AS recipe_name, rb.category, rb.subtype, rb.description, rb.notes,
                   e.name AS equipment_name
            FROM process_sheet_block psb
            JOIN recipe_block rb ON rb.id = psb.recipe_block_id
            JOIN equipment e ON e.id = rb.equipment_id
            WHERE psb.process_sheet_id = ?
            ORDER BY psb.seq, psb.id
            """,
            (process_sheet_id,),
        ).fetchall()
    blocks = _rows_to_dicts(rows)
    for block in blocks:
        block["parameters"] = list_recipe_parameters(block["recipe_block_id"])
    return blocks


def create_process_sheet(data: dict[str, Any]) -> dict[str, Any]:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO process_sheet(title, author, project_name, supervisor, description, status)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                data["title"].strip(),
                data.get("author", "").strip(),
                data.get("project_name", "").strip(),
                data.get("supervisor", "").strip(),
                data.get("description", "").strip(),
                _normalize_status(data.get("status", "draft"), SHEET_STATUSES, "draft"),
            ),
        )
        process_sheet_id = cur.lastrowid
        _replace_process_sheet_blocks(conn, process_sheet_id, data.get("blocks", []))
        snapshot = {
            "id": process_sheet_id,
            "title": data["title"].strip(),
            "author": data.get("author", "").strip(),
            "project_name": data.get("project_name", "").strip(),
            "supervisor": data.get("supervisor", "").strip(),
            "description": data.get("description", "").strip(),
            "status": _normalize_status(data.get("status", "draft"), SHEET_STATUSES, "draft"),
            "blocks": data.get("blocks", []),
        }
        log_audit(conn, "process_sheet", process_sheet_id, "create", snapshot)
        log_process_sheet_revision(conn, process_sheet_id, "create", snapshot)
    return get_process_sheet(process_sheet_id) or {}


def update_process_sheet(process_sheet_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    with get_conn() as conn:
        current = conn.execute(
            "SELECT title, author, project_name, supervisor, description, status FROM process_sheet WHERE id = ?",
            (process_sheet_id,),
        ).fetchone()
        if current:
            curr_status = (current["status"] or "").lower()
            if curr_status == "obsolete":
                raise ValueError("Folhas de processo obsoletas nao podem ser modificadas.")
            elif curr_status == "approved":
                new_status = _normalize_status(data.get("status", "draft"), SHEET_STATUSES, "draft")
                if new_status not in ("approved", "obsolete"):
                    raise ValueError("Folhas de processo aprovadas so podem ser alteradas para Obsoletas.")
                
                # Verify if blocks changed
                curr_blocks_rows = conn.execute(
                    "SELECT recipe_block_id, seq, title_override, notes_override FROM process_sheet_block WHERE process_sheet_id = ? ORDER BY seq",
                    (process_sheet_id,),
                ).fetchall()
                curr_blocks = [dict(r) for r in curr_blocks_rows]
                new_blocks = data.get("blocks", [])
                
                blocks_changed = len(curr_blocks) != len(new_blocks)
                if not blocks_changed:
                    for idx, cb in enumerate(curr_blocks):
                        nb = new_blocks[idx]
                        if cb["recipe_block_id"] != int(nb.get("recipe_block_id") or 0):
                            blocks_changed = True
                            break
                        if (cb["title_override"] or "") != (nb.get("title_override") or ""):
                            blocks_changed = True
                            break
                        if (cb["notes_override"] or "") != (nb.get("notes_override") or ""):
                            blocks_changed = True
                            break
                
                # Verify if metadata changed
                meta_changed = (
                    data["title"].strip() != current["title"] or
                    data.get("author", "").strip() != (current["author"] or "") or
                    data.get("project_name", "").strip() != (current["project_name"] or "") or
                    data.get("supervisor", "").strip() != (current["supervisor"] or "") or
                    data.get("description", "").strip() != (current["description"] or "")
                )
                
                if meta_changed or blocks_changed:
                    raise ValueError(
                        "Folhas de processo aprovadas nao podem ser editadas (apenas o status pode ser alterado para Obsoleta)."
                    )
        conn.execute(
            """
            UPDATE process_sheet
            SET title = ?, author = ?, project_name = ?, supervisor = ?,
                description = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                data["title"].strip(),
                data.get("author", "").strip(),
                data.get("project_name", "").strip(),
                data.get("supervisor", "").strip(),
                data.get("description", "").strip(),
                _normalize_status(data.get("status", "draft"), SHEET_STATUSES, "draft"),
                process_sheet_id,
            ),
        )
        _replace_process_sheet_blocks(conn, process_sheet_id, data.get("blocks", []))
        snapshot = {
            "id": process_sheet_id,
            "title": data["title"].strip(),
            "author": data.get("author", "").strip(),
            "project_name": data.get("project_name", "").strip(),
            "supervisor": data.get("supervisor", "").strip(),
            "description": data.get("description", "").strip(),
            "status": _normalize_status(data.get("status", "draft"), SHEET_STATUSES, "draft"),
            "blocks": data.get("blocks", []),
        }
        log_audit(conn, "process_sheet", process_sheet_id, "update", snapshot)
        log_process_sheet_revision(conn, process_sheet_id, "update", snapshot)
    return get_process_sheet(process_sheet_id)


def _replace_process_sheet_blocks(
    conn: sqlite3.Connection, process_sheet_id: int, blocks: list[dict[str, Any]]
) -> None:
    conn.execute("DELETE FROM process_sheet_block WHERE process_sheet_id = ?", (process_sheet_id,))
    for seq, block in enumerate(blocks, start=1):
        recipe_block_id = int(block.get("recipe_block_id") or 0)
        if not recipe_block_id:
            continue
        conn.execute(
            """
            INSERT INTO process_sheet_block(
                process_sheet_id, recipe_block_id, seq, title_override, notes_override
            )
            VALUES(?, ?, ?, ?, ?)
            """,
            (
                process_sheet_id,
                recipe_block_id,
                int(block.get("seq") or seq),
                str(block.get("title_override", "")).strip(),
                str(block.get("notes_override", "")).strip(),
            ),
        )


def delete_process_sheet(process_sheet_id: int) -> None:
    with get_conn() as conn:
        current = conn.execute(
            "SELECT status FROM process_sheet WHERE id = ?",
            (process_sheet_id,),
        ).fetchone()
        if current and (current["status"] or "").lower() == "approved":
            raise ValueError("Approved process sheets cannot be removed")
        current = get_process_sheet(process_sheet_id) or {"id": process_sheet_id}
        conn.execute("DELETE FROM process_sheet WHERE id = ?", (process_sheet_id,))
        log_audit(conn, "process_sheet", process_sheet_id, "delete", current)
        log_process_sheet_revision(conn, process_sheet_id, "delete", current)


def log_generated(process_sheet_id: int, output_path: Path) -> dict[str, Any]:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO generated_sheet(process_sheet_id, output_path) VALUES(?, ?)",
            (process_sheet_id, str(output_path)),
        )
        generated_id = cur.lastrowid
        row = conn.execute(
            """
            SELECT id, process_sheet_id, output_path, created_at
            FROM generated_sheet
            WHERE id = ?
            """,
            (generated_id,),
        ).fetchone()
        log_audit(conn, "generated_sheet", generated_id, "create", {"process_sheet_id": process_sheet_id, "output_path": str(output_path)})
    return _row_to_dict(row) or {}


def list_generated() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT g.id, g.process_sheet_id, g.output_path, g.created_at, ps.title AS process_sheet_title
            FROM generated_sheet g
            LEFT JOIN process_sheet ps ON ps.id = g.process_sheet_id
            ORDER BY g.id DESC
            """
        ).fetchall()
    return _rows_to_dicts(rows)


def sheet_to_xlsx_payload(sheet: dict[str, Any]) -> dict[str, Any]:
    blocks = []
    for idx, block in enumerate(sheet.get("blocks", []), start=1):
        details = []
        for param in block.get("parameters", []):
            value = param.get("value") or "---"
            unit = f" {param['unit']}" if param.get("unit") else ""
            details.append(f"{param['name']}: {value}{unit}")
        description = block.get("description") or ""
        if description:
            details.insert(0, description)
        blocks.append(
            {
                "ordem": idx,
                "numero": str(idx),
                "titulo": block.get("title_override") or block.get("recipe_name") or f"Bloco {idx}",
                "visao_geral": (
                    f"Categoria: {block.get('category', '-')}\n"
                    f"Subtipo: {block.get('subtype', '-')}\n"
                    f"Equipamento: {block.get('equipment_name', '-')}"
                ),
                "detalhes": "\n".join(details) if details else "---",
                "notas": block.get("notes_override") or block.get("notes") or "",
            }
        )
    return {
        "schema_version": 4,
        "sheet_status": sheet.get("status") or "draft",
        "sheet_title": sheet.get("title") or "Folha de processo",
        "supervisor": sheet.get("supervisor") or "---",
        "project_name": sheet.get("project_name") or "---",
        "collab_type": sheet.get("author") or "---",
        "brief_desc": sheet.get("description") or "---",
        "approval_date": "---",
        "blocks": blocks,
    }


def export_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
