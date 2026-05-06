PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS substrate (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE,
  material TEXT NOT NULL,
  diameter_inch REAL,
  thickness_um REAL,
  format TEXT,
  polished_faces TEXT,
  supplier TEXT,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS process_material (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL, -- resist, promoter, developer, metal, solvent, gas
  name TEXT NOT NULL,
  manufacturer TEXT,
  catalog_code TEXT,
  usage_range TEXT,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(kind, name, catalog_code)
);

CREATE TABLE IF NOT EXISTS process_equipment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  model TEXT,
  manufacturer TEXT,
  category TEXT NOT NULL, -- Fabricacao, Inspecao, Metrologia, Infraestrutura
  location TEXT,
  owner TEXT,
  restrictions TEXT,
  parameter_schema_json TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(name, model)
);

CREATE TABLE IF NOT EXISTS process_step (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  seq_default INTEGER,
  description TEXT
);

CREATE TABLE IF NOT EXISTS process_template (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  objective TEXT,
  description TEXT,
  active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS process_template_step (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  template_id INTEGER NOT NULL,
  step_id INTEGER NOT NULL,
  seq INTEGER NOT NULL,
  required INTEGER DEFAULT 1,
  FOREIGN KEY(template_id) REFERENCES process_template(id) ON DELETE CASCADE,
  FOREIGN KEY(step_id) REFERENCES process_step(id),
  UNIQUE(template_id, seq)
);

CREATE TABLE IF NOT EXISTS process_recipe (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  step_id INTEGER NOT NULL,
  equipment_id INTEGER,
  substrate_id INTEGER,
  status TEXT NOT NULL DEFAULT 'validada', -- validada, em_teste, obsoleta
  confidence_level TEXT NOT NULL DEFAULT 'rotina', -- rotina, provisoria, experimental
  validated_by TEXT,
  validated_at TEXT,
  notes TEXT,
  evidence_link TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(step_id) REFERENCES process_step(id),
  FOREIGN KEY(equipment_id) REFERENCES process_equipment(id),
  FOREIGN KEY(substrate_id) REFERENCES substrate(id),
  UNIQUE(name, version)
);

CREATE TABLE IF NOT EXISTS process_recipe_param (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  recipe_id INTEGER NOT NULL,
  key TEXT NOT NULL,
  value TEXT,
  unit TEXT,
  FOREIGN KEY(recipe_id) REFERENCES process_recipe(id) ON DELETE CASCADE,
  UNIQUE(recipe_id, key)
);

CREATE TABLE IF NOT EXISTS process_compatibility (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  template_id INTEGER,
  step_id INTEGER,
  substrate_id INTEGER,
  material_id INTEGER,
  equipment_id INTEGER,
  recipe_id INTEGER,
  allowed INTEGER NOT NULL DEFAULT 1,
  reason TEXT,
  FOREIGN KEY(template_id) REFERENCES process_template(id) ON DELETE CASCADE,
  FOREIGN KEY(step_id) REFERENCES process_step(id),
  FOREIGN KEY(substrate_id) REFERENCES substrate(id),
  FOREIGN KEY(material_id) REFERENCES process_material(id),
  FOREIGN KEY(equipment_id) REFERENCES process_equipment(id),
  FOREIGN KEY(recipe_id) REFERENCES process_recipe(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS process_run (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  template_id INTEGER,
  operator TEXT,
  lot TEXT,
  status TEXT NOT NULL DEFAULT 'rascunho', -- rascunho, executado, aprovado, arquivado
  execution_date TEXT,
  notes TEXT,
  generated_file_path TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(template_id) REFERENCES process_template(id)
);

CREATE TABLE IF NOT EXISTS process_run_step (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  step_id INTEGER NOT NULL,
  recipe_id INTEGER,
  equipment_id INTEGER,
  executed_by TEXT,
  executed_at TEXT,
  result_status TEXT DEFAULT 'ok',
  notes TEXT,
  FOREIGN KEY(run_id) REFERENCES process_run(id) ON DELETE CASCADE,
  FOREIGN KEY(step_id) REFERENCES process_step(id),
  FOREIGN KEY(recipe_id) REFERENCES process_recipe(id),
  FOREIGN KEY(equipment_id) REFERENCES process_equipment(id)
);

CREATE TABLE IF NOT EXISTS process_run_step_value (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_step_id INTEGER NOT NULL,
  key TEXT NOT NULL,
  value TEXT,
  unit TEXT,
  FOREIGN KEY(run_step_id) REFERENCES process_run_step(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS process_audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT NOT NULL,
  entity_id INTEGER,
  action TEXT NOT NULL,
  changed_by TEXT,
  changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
  before_json TEXT,
  after_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_recipe_step_status ON process_recipe(step_id, status);
CREATE INDEX IF NOT EXISTS idx_compat_filter ON process_compatibility(template_id, step_id, substrate_id, allowed);
CREATE INDEX IF NOT EXISTS idx_run_status ON process_run(status, execution_date);
