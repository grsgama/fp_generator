import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / 'fp_data.db'
SCHEMA = BASE / 'schema_v2.sql'


def upsert(cur, table, unique_where, where_values, cols, values):
    row = cur.execute(f"SELECT id FROM {table} WHERE {unique_where}", where_values).fetchone()
    if row:
        return row[0]
    placeholders = ','.join(['?'] * len(cols))
    cur.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})", values)
    return cur.lastrowid


def run():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.executescript(SCHEMA.read_text(encoding='utf-8'))

    # Core steps
    steps = [
        ('substrate', 'Substrato', 0, 'Definicao do substrato e lote'),
        ('cleaning', 'Limpeza quimica', 1, 'Limpeza inicial'),
        ('adhesion', 'Promotor de adesao', 2, 'Aplicacao de promotor'),
        ('coat', 'Aplicacao de resiste', 3, 'Spin coating de resiste'),
        ('exposure', 'Exposicao', 4, 'Exposicao em escritor a laser'),
        ('develop', 'Revelacao', 5, 'Revelacao do resist'),
        ('deposition', 'Deposicao', 6, 'Deposicao metalica'),
        ('liftoff', 'Lift-off', 7, 'Remocao de resist'),
        ('inspection', 'Inspecao', 8, 'Inspecao final')
    ]
    step_ids = {}
    for code, name, seq, desc in steps:
        sid = upsert(cur, 'process_step', 'code = ?', (code,), ['code', 'name', 'seq_default', 'description'], (code, name, seq, desc))
        step_ids[code] = sid

    # Template
    tpl_id = upsert(
        cur,
        'process_template',
        'name = ?',
        ('Litografia para liftoff metalico',),
        ['name', 'objective', 'description', 'active'],
        ('Litografia para liftoff metalico', 'Pads/estruturas metalicas por liftoff', 'Fluxo padrao ARP3740 em Si 2"', 1)
    )

    for seq, code in enumerate(['substrate', 'cleaning', 'adhesion', 'coat', 'exposure', 'develop', 'deposition', 'liftoff', 'inspection']):
        cur.execute(
            "INSERT OR IGNORE INTO process_template_step(template_id, step_id, seq, required) VALUES (?, ?, ?, 1)",
            (tpl_id, step_ids[code], seq)
        )

    # Substrate
    sub_id = upsert(
        cur,
        'substrate',
        'code = ?',
        ('SI-2IN-300UM',),
        ['code', 'material', 'diameter_inch', 'thickness_um', 'format', 'polished_faces', 'supplier', 'notes'],
        ('SI-2IN-300UM', 'Silicio', 2.0, 300.0, 'Circular', '1', '', 'Substrato padrao para fluxo ARP3740')
    )

    # Materials
    mat_prom = upsert(cur, 'process_material', 'kind = ? AND name = ? AND IFNULL(catalog_code,\'\') = IFNULL(?,\'\')',
                      ('promoter', 'AR 300-80', 'AR-300-80'),
                      ['kind', 'name', 'manufacturer', 'catalog_code', 'usage_range', 'notes'],
                      ('promoter', 'AR 300-80', 'Allresist', 'AR-300-80', 'Spin 4000 rpm; bake 180 C', 'Promotor adesao'))
    mat_resist = upsert(cur, 'process_material', 'kind = ? AND name = ? AND IFNULL(catalog_code,\'\') = IFNULL(?,\'\')',
                        ('resist', 'AR-P 3740', 'AR-P-3740'),
                        ['kind', 'name', 'manufacturer', 'catalog_code', 'usage_range', 'notes'],
                        ('resist', 'AR-P 3740', 'Allresist', 'AR-P-3740', 'Spin 4000 rpm; bake 100 C', 'Resist positivo'))
    mat_dev = upsert(cur, 'process_material', 'kind = ? AND name = ? AND IFNULL(catalog_code,\'\') = IFNULL(?,\'\')',
                     ('developer', 'AR 300-47', 'AR-300-47'),
                     ['kind', 'name', 'manufacturer', 'catalog_code', 'usage_range', 'notes'],
                     ('developer', 'AR 300-47', 'Allresist', 'AR-300-47', '120 s P.A.', 'Revelador'))
    mat_metal = upsert(cur, 'process_material', 'kind = ? AND name = ? AND IFNULL(catalog_code,\'\') = IFNULL(?,\'\')',
                       ('metal', 'Ouro', 'Au'),
                       ['kind', 'name', 'manufacturer', 'catalog_code', 'usage_range', 'notes'],
                       ('metal', 'Ouro', '', 'Au', '20 nm sputter', 'Deposicao metalica'))
    mat_solvent = upsert(cur, 'process_material', 'kind = ? AND name = ? AND IFNULL(catalog_code,\'\') = IFNULL(?,\'\')',
                         ('solvent', 'Acetona P.A.', 'ACETONA-PA'),
                         ['kind', 'name', 'manufacturer', 'catalog_code', 'usage_range', 'notes'],
                         ('solvent', 'Acetona P.A.', '', 'ACETONA-PA', 'Lift-off', 'Solvente'))

    # Equipments
    eq_spin = upsert(cur, 'process_equipment', 'name = ? AND IFNULL(model,\'\') = IFNULL(?,\'\')',
                     ('Spin Coater', 'WS-650'),
                     ['name', 'model', 'manufacturer', 'category', 'location', 'owner', 'restrictions', 'parameter_schema_json'],
                     ('Spin Coater', 'WS-650', 'Laurell', 'Fabricação', 'LabNano', '', '', '{}'))
    eq_exp = upsert(cur, 'process_equipment', 'name = ? AND IFNULL(model,\'\') = IFNULL(?,\'\')',
                    ('Maskless Lithography', 'DWL 66+'),
                    ['name', 'model', 'manufacturer', 'category', 'location', 'owner', 'restrictions', 'parameter_schema_json'],
                    ('Maskless Lithography', 'DWL 66+', 'Heidelberg Instruments', 'Fabricação', 'LabNano', '', '', '{}'))
    eq_sput = upsert(cur, 'process_equipment', 'name = ? AND IFNULL(model,\'\') = IFNULL(?,\'\')',
                     ('Sputtering System', 'AJA Sputtering (sala limpa)'),
                     ['name', 'model', 'manufacturer', 'category', 'location', 'owner', 'restrictions', 'parameter_schema_json'],
                     ('Sputtering System', 'AJA Sputtering (sala limpa)', 'AJA International', 'Fabricação', 'LabNano', '', '', '{}'))
    eq_insp = upsert(cur, 'process_equipment', 'name = ? AND IFNULL(model,\'\') = IFNULL(?,\'\')',
                     ('Probe Station', 'PA200'),
                     ['name', 'model', 'manufacturer', 'category', 'location', 'owner', 'restrictions', 'parameter_schema_json'],
                     ('Probe Station', 'PA200', 'FormFactor / Cascade Microtech', 'Inspeção', 'LabNano', '', '', '{}'))

    # Recipes (pilot flow)
    rec_prom = upsert(cur, 'process_recipe', 'name = ? AND version = ?',
                      ('PROMOTOR_AR30080_4000RPM_180C_4MIN', 1),
                      ['name', 'version', 'step_id', 'equipment_id', 'substrate_id', 'status', 'confidence_level', 'validated_by', 'validated_at', 'notes', 'evidence_link'],
                      ('PROMOTOR_AR30080_4000RPM_180C_4MIN', 1, step_ids['adhesion'], eq_spin, sub_id, 'validada', 'rotina', 'LabNano', '2026-03-24', '', ''))
    rec_coat = upsert(cur, 'process_recipe', 'name = ? AND version = ?',
                      ('COAT_ARP3740_4000RPM_100C_1MIN', 1),
                      ['name', 'version', 'step_id', 'equipment_id', 'substrate_id', 'status', 'confidence_level', 'validated_by', 'validated_at', 'notes', 'evidence_link'],
                      ('COAT_ARP3740_4000RPM_100C_1MIN', 1, step_ids['coat'], eq_spin, sub_id, 'validada', 'rotina', 'LabNano', '2026-03-24', '', ''))
    rec_exp = upsert(cur, 'process_recipe', 'name = ? AND version = ?',
                     ('EXPO_DWL66_INT45_50_FOCUS_M2_P4', 1),
                     ['name', 'version', 'step_id', 'equipment_id', 'substrate_id', 'status', 'confidence_level', 'validated_by', 'validated_at', 'notes', 'evidence_link'],
                     ('EXPO_DWL66_INT45_50_FOCUS_M2_P4', 1, step_ids['exposure'], eq_exp, sub_id, 'validada', 'provisoria', 'LabNano', '2026-03-24', 'Foco ideal 0-2', ''))
    rec_dev = upsert(cur, 'process_recipe', 'name = ? AND version = ?',
                     ('DEV_AR30047_PA_120S_PUDDLE', 1),
                     ['name', 'version', 'step_id', 'equipment_id', 'substrate_id', 'status', 'confidence_level', 'validated_by', 'validated_at', 'notes', 'evidence_link'],
                     ('DEV_AR30047_PA_120S_PUDDLE', 1, step_ids['develop'], eq_spin, sub_id, 'validada', 'rotina', 'LabNano', '2026-03-24', '', ''))
    rec_dep = upsert(cur, 'process_recipe', 'name = ? AND version = ?',
                     ('DEP_AU_20NM_SPUTTER', 1),
                     ['name', 'version', 'step_id', 'equipment_id', 'substrate_id', 'status', 'confidence_level', 'validated_by', 'validated_at', 'notes', 'evidence_link'],
                     ('DEP_AU_20NM_SPUTTER', 1, step_ids['deposition'], eq_sput, sub_id, 'validada', 'rotina', 'LabNano', '2026-03-24', '', ''))
    rec_lif = upsert(cur, 'process_recipe', 'name = ? AND version = ?',
                     ('LIFTOFF_ACETONA_AGIT_US_SHORT', 1),
                     ['name', 'version', 'step_id', 'equipment_id', 'substrate_id', 'status', 'confidence_level', 'validated_by', 'validated_at', 'notes', 'evidence_link'],
                     ('LIFTOFF_ACETONA_AGIT_US_SHORT', 1, step_ids['liftoff'], None, sub_id, 'validada', 'rotina', 'LabNano', '2026-03-24', '', ''))

    params = {
        rec_prom: [('promoter', 'AR 300-80', ''), ('spin_rpm', '4000', 'rpm'), ('bake_temp', '180', 'C'), ('bake_time', '4', 'min')],
        rec_coat: [('resist', 'AR-P 3740', ''), ('spin_rpm', '4000', 'rpm'), ('bake_temp', '100', 'C'), ('bake_time', '1', 'min')],
        rec_exp: [('intensity_min', '45', '%'), ('intensity_max', '50', '%'), ('focus_min', '-2', ''), ('focus_max', '+4', ''), ('focus_ideal', '0-2', '')],
        rec_dev: [('developer', 'AR 300-47', ''), ('dilution', 'P.A.', ''), ('develop_time', '120', 's'), ('mode', 'puddle', '')],
        rec_dep: [('metal', 'Au', ''), ('thickness', '20', 'nm'), ('method', 'sputtering bancada', '')],
        rec_lif: [('solvent', 'Acetona P.A.', ''), ('agitation', 'circular', ''), ('ultrasonic', 'few seconds', '')],
    }
    for rid, plist in params.items():
        for key, val, unit in plist:
            cur.execute(
                "INSERT OR IGNORE INTO process_recipe_param(recipe_id, key, value, unit) VALUES (?, ?, ?, ?)",
                (rid, key, val, unit)
            )

    # Compatibility rules for pilot flow
    rules = [
        (tpl_id, step_ids['adhesion'], sub_id, mat_prom, eq_spin, rec_prom, 1, 'Fluxo padrao ARP3740 em Si 2"'),
        (tpl_id, step_ids['coat'], sub_id, mat_resist, eq_spin, rec_coat, 1, 'Fluxo padrao ARP3740 em Si 2"'),
        (tpl_id, step_ids['exposure'], sub_id, mat_resist, eq_exp, rec_exp, 1, 'Faixa validada de intensidade/foco'),
        (tpl_id, step_ids['develop'], sub_id, mat_dev, eq_spin, rec_dev, 1, 'Revelacao padrao'),
        (tpl_id, step_ids['deposition'], sub_id, mat_metal, eq_sput, rec_dep, 1, 'Deposicao padrao de Au'),
        (tpl_id, step_ids['liftoff'], sub_id, mat_solvent, None, rec_lif, 1, 'Lift-off padrao com acetona'),
    ]
    for tpl, step, sub, mat, eq, rec, allowed, reason in rules:
        cur.execute(
            """
            INSERT OR IGNORE INTO process_compatibility(
              template_id, step_id, substrate_id, material_id, equipment_id, recipe_id, allowed, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (tpl, step, sub, mat, eq, rec, allowed, reason)
        )

    conn.commit()

    # summary
    def count(t):
        return cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]

    print('Schema/seed aplicado com sucesso:')
    for t in [
        'substrate', 'process_material', 'process_equipment', 'process_step',
        'process_template', 'process_template_step', 'process_recipe',
        'process_recipe_param', 'process_compatibility'
    ]:
        print(f'- {t}: {count(t)} registros')

    conn.close()


if __name__ == '__main__':
    run()
