import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "fp_data.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                model TEXT,
                manufacturer TEXT,
                category TEXT DEFAULT 'Fabricação',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS recipe (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                data_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS generated_sheet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER,
                equipment_id INTEGER,
                output_path TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(recipe_id) REFERENCES recipe(id),
                FOREIGN KEY(equipment_id) REFERENCES equipment(id)
            );
            """
        )
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(equipment)").fetchall()]
        if "category" not in cols:
            conn.execute("ALTER TABLE equipment ADD COLUMN category TEXT DEFAULT 'Fabricação'")


def list_equipment():
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, name, model, manufacturer, category, notes, created_at FROM equipment ORDER BY category, name, id"
        ).fetchall()


def add_equipment(name, model, manufacturer, category, notes):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO equipment(name, model, manufacturer, category, notes) VALUES(?, ?, ?, ?, ?)",
            (name.strip(), model.strip(), manufacturer.strip(), category.strip(), notes.strip()),
        )


def delete_equipment(equipment_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))


def list_recipes():
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, name, description, data_json, created_at FROM recipe ORDER BY id DESC"
        ).fetchall()


def add_recipe(name, description, data_json):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO recipe(name, description, data_json) VALUES(?, ?, ?)",
            (name.strip(), description.strip(), data_json),
        )


def delete_recipe(recipe_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM recipe WHERE id = ?", (recipe_id,))


def log_generated(recipe_id, equipment_id, output_path):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO generated_sheet(recipe_id, equipment_id, output_path) VALUES(?, ?, ?)",
            (recipe_id, equipment_id, str(output_path)),
        )


def list_generated():
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT g.id, g.output_path, g.created_at, r.name AS recipe_name, e.name AS equipment_name
            FROM generated_sheet g
            LEFT JOIN recipe r ON r.id = g.recipe_id
            LEFT JOIN equipment e ON e.id = g.equipment_id
            ORDER BY g.id DESC
            """
        ).fetchall()
