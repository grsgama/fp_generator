from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import streamlit as st

import db
from xlsx_writer import fill_sheet

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_CANDIDATES = [
    BASE_DIR.parent / "FP_FolhaDeProcesso_Modelo_EmBranco.xlsx",
    Path("/home/grsgama/Nextcloud/LabNano/Folha de Processo/FP_FolhaDeProcesso_Modelo_EmBranco.xlsx"),
]
DEFAULT_TEMPLATE = next((p for p in TEMPLATE_CANDIDATES if p.exists()), TEMPLATE_CANDIDATES[0])
OUTPUT_DIR = BASE_DIR / "outputs"

DEFAULT_BLOCKS = [
    {
        "ordem": 1,
        "titulo": "Substrato",
        "visao_geral": "Sistema: ---\nUsuário: ---\nTempo de máquina [hrs]: ---\nTempo de uso [hrs]: ---\nData de conclusão: ---",
        "detalhes": "Nome da amostra: ---\nMaterial: ---\nEspessura do substrato: ---\nNúmero de substratos: ---\nFormato: ---\nTamanho do substrato: ---\nFaces polidas: ---\nNúmero de série da caixa: ---",
        "notas": "",
    },
    {
        "ordem": 2,
        "titulo": "Limpeza química",
        "visao_geral": "Sistema: ---\nUsuário: ---\nTempo de máquina [hrs]: ---\nTempo de uso [hrs]: ---\nData de conclusão: ---",
        "detalhes": "Nome da amostra: ---\n\nEtapa 1:\nRecipiente de limpeza: ---\nProduto: ---\nTempo: ---\nAquecimento: ---\nSecagem: ---",
        "notas": "",
    },
    {
        "ordem": 3,
        "titulo": "Promotor de adesão",
        "visao_geral": "Sistema: ---\nUsuário: ---\nTempo de máquina [min]: ---\nTempo de uso [min]: ---\nData de conclusão: ---",
        "detalhes": "Material aplicado: ---\nReceita: ---\nVelocidades e tempos: ---\nTemperatura: ---\nTempo: ---",
        "notas": "",
    },
    {
        "ordem": 4,
        "titulo": "Aplicação de resiste",
        "visao_geral": "Sistema: ---\nUsuário: ---\nTempo de máquina [hrs]: ---\nTempo de uso [hrs]: ---\nData de conclusão: ---",
        "detalhes": "Umidade e temperatura da sala: ---\nLado da aplicação: ---\nMaterial aplicado: ---\nEspessura estimada: ---\nReceita: ---\nVelocidades e tempos: ---\nTemp. prato quente (°C): ---\nTempo prato quente (min): ---",
        "notas": "",
    },
    {
        "ordem": 5,
        "titulo": "Exposição",
        "visao_geral": "Sistema: ---\nUsuário: ---\nTempo de máquina [min]: ---\nTempo de uso [min]: ---\nData de conclusão: ---",
        "detalhes": "Umidade e temperatura: ---\nNome do arquivo de exposição: ---\nMenor resolução do desenho: ---\nLado exposto: ---\nMaterial exposto: ---\nExposição: ---\nPotência (mW): ---\nIntensidade (%): ---\nFoco: ---\nAlinhamento: ---",
        "notas": "",
    },
    {
        "ordem": 6,
        "titulo": "Revelação",
        "visao_geral": "Sistema: ---\nUsuário: ---\nTempo de máquina [min]: ---\nTempo de uso [min]: ---\nData de conclusão: ---",
        "detalhes": "Umidade e temperatura da sala: ---\nRecipiente: ---\nMaterial revelado: ---\nRevelador: ---\nDiluição: ---\nTempo de revelação: ---\nVolume usado: ---\nStopper: ---",
        "notas": "",
    },
    {
        "ordem": 7,
        "titulo": "Deposição",
        "visao_geral": "Sistema: ---\nUsuário: ---\nTempo de máquina [min]: ---\nTempo de uso [min]: ---\nData de conclusão: ---",
        "detalhes": "Umidade e temperatura da sala: ---\nMaterial depositado: ---\nTempo de deposição (s): ---\nTaxa (A/s): ---\nReceita: ---",
        "notas": "",
    },
    {
        "ordem": 8,
        "titulo": "Lift-off",
        "visao_geral": "Sistema: ---\nUsuário: ---\nTempo de máquina [min]: ---\nTempo de uso [min]: ---\nData de conclusão: ---",
        "detalhes": "Umidade e temperatura da sala: ---\nMaterial depositado: ---\nRecipiente: ---\nTempo (s): ---\nForma: ---",
        "notas": "",
    },
    {
        "ordem": 9,
        "titulo": "Inspeção",
        "visao_geral": "Sistema: ---\nUsuário: ---\nTempo de máquina [min]: ---\nTempo de uso [min]: ---\nData de conclusão: ---",
        "detalhes": "Umidade e temperatura da sala: ---\nAmostra: ---\nTipo de foco: ---\nValor do foco: ---\nAlinhamento: ---\nTécnica utilizada: ---\nLocal de armazenamento: ---",
        "notas": "---",
    },
]

BLOCK_LIBRARY = {
    "substrato": {
        "label": "Substrato",
        "kind": "simple",
        "block": DEFAULT_BLOCKS[0],
    },
    "limpeza_quimica": {
        "label": "Limpeza química",
        "kind": "simple",
        "block": DEFAULT_BLOCKS[1],
    },
    "litografia_optica": {
        "label": "Litografia óptica",
        "kind": "compound",
        "children": [
            DEFAULT_BLOCKS[2],
            DEFAULT_BLOCKS[3],
            DEFAULT_BLOCKS[4],
            DEFAULT_BLOCKS[5],
            {
                "ordem": 7,
                "titulo": "Inspeção pós-litografia",
                "visao_geral": "Sistema: Microscópio óptico\nUsuário: ---\nTempo de máquina [min]: ---\nTempo de uso [min]: ---\nData de conclusão: ---",
                "detalhes": "Amostra: ---\nTécnica utilizada: inspeção óptica\nCritério: verificar abertura, foco, resíduos e aderência do resiste\nLocal de armazenamento: ---",
                "notas": "",
            },
        ],
    },
    "deposicao": {
        "label": "Deposição",
        "kind": "simple",
        "block": DEFAULT_BLOCKS[6],
    },
    "liftoff": {
        "label": "Lift-off",
        "kind": "simple",
        "block": DEFAULT_BLOCKS[7],
    },
    "inspecao": {
        "label": "Inspeção",
        "kind": "simple",
        "block": DEFAULT_BLOCKS[8],
    },
    "etching": {
        "label": "Etching",
        "kind": "simple",
        "block": {
            "ordem": 1,
            "titulo": "Etching",
            "visao_geral": "Sistema: ---\nUsuário: ---\nTempo de máquina [min]: ---\nTempo de uso [min]: ---\nData de conclusão: ---",
            "detalhes": "Material atacado: ---\nMáscara: ---\nReceita: ---\nGases/química: ---\nPotência: ---\nPressão: ---\nTempo: ---\nTaxa de ataque: ---",
            "notas": "",
        },
    },
}

PROCESS_PRESETS = {
    "Em branco": [],
    "Lift-off": ["substrato", "limpeza_quimica", "litografia_optica", "deposicao", "liftoff"],
    "Litografia óptica": ["substrato", "limpeza_quimica", "litografia_optica"],
    "Deposição simples": ["substrato", "limpeza_quimica", "deposicao", "inspecao"],
    "Etching": ["substrato", "limpeza_quimica", "litografia_optica", "etching", "inspecao"],
}

LEGACY_BLOCK_KEYS = [
    ("Substrato", "substrate_overview", "substrate_details", ""),
    ("Limpeza química", "cleaning_overview", "cleaning_details", ""),
    ("Aplicação de resiste", "resist1_overview", "resist1_details", ""),
    ("Aplicação de resiste", "resist2_overview", "resist2_details", ""),
    ("Exposição", "exposure_overview", "exposure_details", ""),
    ("Revelação", "develop_overview", "develop_details", ""),
    ("Deposição", "deposition_overview", "deposition_details", ""),
    ("Lift-off", "liftoff_overview", "liftoff_details", ""),
    ("Inspeção", "inspection_overview", "inspection_details", "inspection_notes"),
]


def init():
    db.init_db()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def equipment_tab():
    st.subheader("Equipamentos")
    with st.form("add_equipment"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Nome do equipamento", placeholder="Ex.: Dicing saw")
        model = c2.text_input("Modelo", placeholder="Ex.: DAD3241")
        c3, c4, c5 = st.columns(3)
        manufacturer = c3.text_input("Fabricante", placeholder="Ex.: DISCO")
        category = c4.selectbox("Categoria", ["Fabricação", "Inspeção", "Metrologia", "Infraestrutura"])
        notes = c5.text_input("Observações")
        submitted = st.form_submit_button("Salvar equipamento")
        if submitted:
            if not name.strip():
                st.error("Nome do equipamento é obrigatório.")
            else:
                db.add_equipment(name, model, manufacturer, category, notes)
                st.success("Equipamento salvo.")

    rows = db.list_equipment()
    if not rows:
        st.info("Nenhum equipamento cadastrado ainda.")
    else:
        st.write("### Cadastrados")
        for r in rows:
            with st.expander(f"#{r['id']} - [{r['category'] or '-'}] {r['name']} ({r['model'] or '-'})"):
                st.write(f"Fabricante: {r['manufacturer'] or '-'}")
                st.write(f"Categoria: {r['category'] or '-'}")
                st.write(f"Notas: {r['notes'] or '-'}")
                if st.button("Excluir", key=f"del_eq_{r['id']}"):
                    db.delete_equipment(r["id"])
                    st.rerun()


def _multiline(label, placeholder=""):
    return st.text_area(label, placeholder=placeholder, height=100)


def _normalize_blocks(rows):
    blocks = []
    for idx, row in enumerate(rows or [], start=1):
        number = str(row.get("numero") or "").strip()
        title = str(row.get("titulo") or "").strip()
        overview = str(row.get("visao_geral") or "").strip()
        details = str(row.get("detalhes") or "").strip()
        notes = str(row.get("notas") or "").strip()
        if not any([title, overview, details, notes]):
            continue
        try:
            order = int(row.get("ordem") or idx)
        except (TypeError, ValueError):
            order = idx
        blocks.append(
            {
                "ordem": order,
                "numero": number or str(order),
                "titulo": title or f"Bloco {idx}",
                "visao_geral": overview,
                "detalhes": details,
                "notas": notes,
            }
        )
    return sorted(blocks, key=lambda b: b["ordem"])


def _block_copy(block, order, number, title_prefix=""):
    copied = {
        "ordem": order,
        "numero": str(number),
        "titulo": block.get("titulo", ""),
        "visao_geral": block.get("visao_geral", ""),
        "detalhes": block.get("detalhes", ""),
        "notas": block.get("notas", ""),
    }
    if title_prefix:
        copied["titulo"] = f"{title_prefix} / {copied['titulo']}"
    return copied


def expand_library_item(key, step_number, order_start):
    item = BLOCK_LIBRARY[key]
    if item["kind"] == "simple":
        return [_block_copy(item["block"], order_start, step_number)]

    blocks = []
    for child_idx, child in enumerate(item["children"], start=1):
        blocks.append(
            _block_copy(
                child,
                order_start + child_idx - 1,
                f"{step_number}.{child_idx}",
                item["label"],
            )
        )
    return blocks


def build_blocks_from_keys(keys):
    blocks = []
    order = 1
    for step_number, key in enumerate(keys, start=1):
        expanded = expand_library_item(key, step_number, order)
        blocks.extend(expanded)
        order += len(expanded)
    return blocks


def resequence_blocks(blocks):
    normalized = _normalize_blocks(blocks)
    for idx, block in enumerate(normalized, start=1):
        block["ordem"] = idx
        if not block.get("numero"):
            block["numero"] = str(idx)
    return normalized


def block_editor(blocks, key):
    return st.data_editor(
        blocks,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=key,
        column_config={
            "ordem": st.column_config.NumberColumn("Ordem interna", min_value=1, step=1, width="small"),
            "numero": st.column_config.TextColumn("Nº na FP", width="small"),
            "titulo": st.column_config.TextColumn("Bloco", width="medium"),
            "visao_geral": st.column_config.TextColumn("Visão geral", width="large"),
            "detalhes": st.column_config.TextColumn("Detalhes", width="large"),
            "notas": st.column_config.TextColumn("Notas", width="medium"),
        },
    )


def payload_blocks(payload):
    if payload.get("blocks"):
        return _normalize_blocks(payload["blocks"])

    blocks = []
    for idx, (title, overview_key, details_key, notes_key) in enumerate(LEGACY_BLOCK_KEYS, start=1):
        overview = payload.get(overview_key, "")
        details = payload.get(details_key, "")
        notes = payload.get(notes_key, "") if notes_key else ""
        if any([overview, details, notes]):
            blocks.append(
                {
                    "ordem": idx,
                    "titulo": title,
                    "visao_geral": overview,
                    "detalhes": details,
                    "notas": notes,
                }
            )
    return blocks


def recipe_tab():
    st.subheader("Receitas / Blocos")

    with st.form("add_recipe"):
        name = st.text_input("Nome da receita", placeholder="Ex.: Processo Au com ARP3740")
        description = st.text_input("Descrição curta")

        st.write("#### Cabeçalho")
        c1, c2 = st.columns(2)
        sheet_title = c1.text_input("Título da folha", value="Folha em branco")
        supervisor = c2.text_input("Orientador/Supervisor", value="---")
        c3, c4 = st.columns(2)
        project_name = c3.text_input("Projeto", value="---")
        collab_type = c4.text_input("Tipo de colaboração", value="---")
        brief_desc = st.text_input("Breve descrição", value="---")
        approval_date = st.date_input("Data de aprovação", value=date.today())

        st.write("#### Blocos do processo")
        blocks = block_editor(
            DEFAULT_BLOCKS,
            "recipe_blocks_editor",
        )

        save = st.form_submit_button("Salvar receita")
        if save:
            if not name.strip():
                st.error("Nome da receita é obrigatório.")
            else:
                normalized_blocks = _normalize_blocks(blocks)
                if not normalized_blocks:
                    st.error("Inclua ao menos um bloco de processo.")
                    return
                payload = {
                    "schema_version": 2,
                    "sheet_title": sheet_title,
                    "supervisor": supervisor,
                    "project_name": project_name,
                    "collab_type": collab_type,
                    "brief_desc": brief_desc,
                    "approval_date": approval_date.strftime("%d/%m/%Y"),
                    "blocks": normalized_blocks,
                }
                db.add_recipe(name, description, json.dumps(payload, ensure_ascii=False))
                st.success("Receita salva.")

    st.write("### Receitas salvas")
    for r in db.list_recipes():
        with st.expander(f"#{r['id']} - {r['name']}"):
            st.write(r["description"] or "-")
            try:
                payload = json.loads(r["data_json"])
                blocks = payload_blocks(payload)
                st.caption(f"{len(blocks)} bloco(s) de processo")
            except json.JSONDecodeError:
                st.caption("Receita com dados inválidos")
            if st.button("Excluir receita", key=f"del_recipe_{r['id']}"):
                db.delete_recipe(r["id"])
                st.rerun()


def generate_tab():
    st.subheader("Montar e gerar folha de processo")

    recipes = db.list_recipes()
    equipment = db.list_equipment()

    if "assembly_blocks" not in st.session_state:
        st.session_state.assembly_blocks = build_blocks_from_keys(PROCESS_PRESETS["Lift-off"])

    st.write("#### Cabeçalho")
    c1, c2 = st.columns(2)
    sheet_title = c1.text_input("Título da folha", value="Folha de processo")
    supervisor = c2.text_input("Orientador/Supervisor", value="---")
    c3, c4 = st.columns(2)
    project_name = c3.text_input("Projeto", value="---")
    collab_type = c4.text_input("Tipo de colaboração", value="---")
    brief_desc = st.text_input("Breve descrição", value="---")
    approval_date = st.date_input("Data de aprovação", value=date.today())

    st.write("#### Montagem por blocos")
    p1, p2, p3 = st.columns([2, 2, 1])
    preset_name = p1.selectbox("Processo base", options=list(PROCESS_PRESETS.keys()), index=1)
    if p1.button("Carregar processo base"):
        st.session_state.assembly_blocks = build_blocks_from_keys(PROCESS_PRESETS[preset_name])
        st.rerun()

    block_key = p2.selectbox(
        "Adicionar bloco da biblioteca",
        options=list(BLOCK_LIBRARY.keys()),
        format_func=lambda key: BLOCK_LIBRARY[key]["label"],
    )
    if p2.button("Adicionar bloco"):
        current = resequence_blocks(st.session_state.assembly_blocks)
        next_step = len({str(b.get("numero", "")).split(".")[0] for b in current if b.get("numero")}) + 1
        st.session_state.assembly_blocks = current + expand_library_item(block_key, next_step, len(current) + 1)
        st.rerun()

    if p3.button("Limpar sequência"):
        st.session_state.assembly_blocks = []
        st.rerun()

    edited_blocks = block_editor(st.session_state.assembly_blocks, "assembly_blocks_editor")
    normalized_blocks = resequence_blocks(edited_blocks)
    st.session_state.assembly_blocks = normalized_blocks

    st.write("#### Usar receita salva como ponto de partida")
    if recipes:
        r1, r2 = st.columns([3, 1])
        recipe_id_to_load = r1.selectbox(
            "Receita salva",
            options=[r["id"] for r in recipes],
            format_func=lambda rid: next(r["name"] for r in recipes if r["id"] == rid),
        )
        if r2.button("Carregar receita"):
            recipe = next(r for r in recipes if r["id"] == recipe_id_to_load)
            payload = json.loads(recipe["data_json"])
            st.session_state.assembly_blocks = payload_blocks(payload)
            st.rerun()
    else:
        st.caption("Nenhuma receita salva encontrada. Você ainda pode montar a FP por blocos.")

    st.write("#### Equipamento e saída")
    e1, e2, e3 = st.columns(3)
    categories = sorted({(e["category"] or "Sem categoria") for e in equipment})
    selected_category = e1.selectbox(
        "Categoria do equipamento",
        options=["Todas"] + categories,
    )
    filtered_equipment = (
        equipment
        if selected_category == "Todas"
        else [e for e in equipment if (e["category"] or "Sem categoria") == selected_category]
    )
    equipment_id = e2.selectbox(
        "Equipamento",
        options=[0] + [e["id"] for e in filtered_equipment],
        format_func=lambda eid: "(nenhum)"
        if eid == 0
        else f"{next(e['name'] for e in filtered_equipment if e['id'] == eid)} [{next(e['category'] or '-' for e in filtered_equipment if e['id'] == eid)}]",
    )

    e3.caption(f"Equipamentos visíveis: {len(filtered_equipment)}")

    template_path = st.text_input("Template XLSX", value=str(DEFAULT_TEMPLATE))
    filename = st.text_input("Nome do arquivo de saída", value=f"FP_gerada_{date.today().strftime('%Y%m%d')}.xlsx")

    st.write("#### Salvar composição")
    s1, s2, s3 = st.columns([2, 3, 1])
    save_name = s1.text_input("Nome para salvar", placeholder="Ex.: Lift-off Ti 50 nm em Si")
    save_description = s2.text_input("Descrição para salvar", placeholder="Ex.: Substrato Si, litografia óptica, sputtering Ti 50 nm e lift-off")
    if s3.button("Salvar FP"):
        if not save_name.strip():
            st.error("Informe um nome para salvar a composição.")
        elif not normalized_blocks:
            st.error("Inclua ao menos um bloco antes de salvar.")
        else:
            payload = {
                "schema_version": 3,
                "composition_mode": "blocks",
                "sheet_title": sheet_title,
                "supervisor": supervisor,
                "project_name": project_name,
                "collab_type": collab_type,
                "brief_desc": brief_desc,
                "approval_date": approval_date.strftime("%d/%m/%Y"),
                "blocks": normalized_blocks,
            }
            db.add_recipe(save_name, save_description, json.dumps(payload, ensure_ascii=False))
            st.success("Composição salva como receita reutilizável.")

    if st.button("Gerar folha", type="primary"):
        template = Path(template_path)
        if not template.exists():
            st.error(f"Template não encontrado: {template}")
            return

        if not normalized_blocks:
            st.error("Inclua ao menos um bloco de processo.")
            return

        payload = {
            "schema_version": 3,
            "composition_mode": "blocks",
            "sheet_title": sheet_title,
            "supervisor": supervisor,
            "project_name": project_name,
            "collab_type": collab_type,
            "brief_desc": brief_desc,
            "approval_date": approval_date.strftime("%d/%m/%Y"),
            "blocks": normalized_blocks,
        }

        if equipment_id != 0:
            eq = next(e for e in equipment if e["id"] == equipment_id)
            enrich = (
                f"Equipamento: {eq['name']} | Modelo: {eq['model'] or '-'} | "
                f"Fabricante: {eq['manufacturer'] or '-'} | Categoria: {eq['category'] or '-'}"
            )
            base_desc = payload.get("brief_desc", "")
            payload["brief_desc"] = f"{base_desc} | {enrich}" if base_desc else enrich

        output_path = OUTPUT_DIR / filename
        fill_sheet(template, output_path, payload)
        db.log_generated(None, equipment_id if equipment_id != 0 else None, output_path)

        st.success(f"Planilha gerada: {output_path}")
        with output_path.open("rb") as f:
            st.download_button("Baixar arquivo", f, file_name=output_path.name)

    st.write("### Histórico")
    for g in db.list_generated():
        st.write(f"#{g['id']} | {g['created_at']} | {g['recipe_name'] or '-'} | {g['equipment_name'] or '-'}")


def main():
    init()
    st.set_page_config(page_title="Gerador de Folha de Processo", layout="wide")
    st.title("Gerador de Folha de Processo")
    st.caption("MVP local - SQLite + template XLSX com formatação preservada")

    tab1, tab2, tab3 = st.tabs(["Equipamentos", "Receitas", "Gerar planilha"])
    with tab1:
        equipment_tab()
    with tab2:
        recipe_tab()
    with tab3:
        generate_tab()


if __name__ == "__main__":
    main()
