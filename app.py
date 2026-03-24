from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import streamlit as st

import db
from xlsx_writer import fill_sheet

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = BASE_DIR.parent / "FP_FolhaDeProcesso_Modelo_EmBranco.xlsx"
OUTPUT_DIR = BASE_DIR / "outputs"


def init():
    db.init_db()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def equipment_tab():
    st.subheader("Equipamentos")
    with st.form("add_equipment"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Nome do equipamento", placeholder="Ex.: Dicing saw")
        model = c2.text_input("Modelo", placeholder="Ex.: DAD3241")
        c3, c4 = st.columns(2)
        manufacturer = c3.text_input("Fabricante", placeholder="Ex.: DISCO")
        notes = c4.text_input("Observações")
        submitted = st.form_submit_button("Salvar equipamento")
        if submitted:
            if not name.strip():
                st.error("Nome do equipamento é obrigatório.")
            else:
                db.add_equipment(name, model, manufacturer, notes)
                st.success("Equipamento salvo.")

    rows = db.list_equipment()
    if not rows:
        st.info("Nenhum equipamento cadastrado ainda.")
    else:
        st.write("### Cadastrados")
        for r in rows:
            with st.expander(f"#{r['id']} - {r['name']} ({r['model'] or '-'})"):
                st.write(f"Fabricante: {r['manufacturer'] or '-'}")
                st.write(f"Notas: {r['notes'] or '-'}")
                if st.button("Excluir", key=f"del_eq_{r['id']}"):
                    db.delete_equipment(r["id"])
                    st.rerun()


def _multiline(label, placeholder=""):
    return st.text_area(label, placeholder=placeholder, height=100)


def recipe_tab():
    st.subheader("Receitas / Parâmetros")

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

        st.write("#### Etapas")
        substrate_overview = _multiline("Substrato - visão geral", "Sistema/usuário/tempo/data")
        substrate_details = _multiline("Substrato - detalhes", "Material, espessura, tamanho...")
        cleaning_overview = _multiline("Limpeza - visão geral")
        cleaning_details = _multiline("Limpeza - detalhes")
        resist1_overview = _multiline("Aplicação 1 - visão geral")
        resist1_details = _multiline("Aplicação 1 - detalhes")
        resist2_overview = _multiline("Aplicação 2 - visão geral")
        resist2_details = _multiline("Aplicação 2 - detalhes")
        exposure_overview = _multiline("Exposição - visão geral")
        exposure_details = _multiline("Exposição - detalhes")
        develop_overview = _multiline("Revelação - visão geral")
        develop_details = _multiline("Revelação - detalhes")
        deposition_overview = _multiline("Deposição - visão geral")
        deposition_details = _multiline("Deposição - detalhes")
        liftoff_overview = _multiline("Lift-off - visão geral")
        liftoff_details = _multiline("Lift-off - detalhes")
        inspection_overview = _multiline("Inspeção - visão geral")
        inspection_details = _multiline("Inspeção - detalhes")
        inspection_notes = st.text_input("Notas (coluna F da inspeção)", value="---")

        save = st.form_submit_button("Salvar receita")
        if save:
            if not name.strip():
                st.error("Nome da receita é obrigatório.")
            else:
                payload = {
                    "sheet_title": sheet_title,
                    "supervisor": supervisor,
                    "project_name": project_name,
                    "collab_type": collab_type,
                    "brief_desc": brief_desc,
                    "approval_date": approval_date.strftime("%d/%m/%Y"),
                    "substrate_overview": substrate_overview,
                    "substrate_details": substrate_details,
                    "cleaning_overview": cleaning_overview,
                    "cleaning_details": cleaning_details,
                    "resist1_overview": resist1_overview,
                    "resist1_details": resist1_details,
                    "resist2_overview": resist2_overview,
                    "resist2_details": resist2_details,
                    "exposure_overview": exposure_overview,
                    "exposure_details": exposure_details,
                    "develop_overview": develop_overview,
                    "develop_details": develop_details,
                    "deposition_overview": deposition_overview,
                    "deposition_details": deposition_details,
                    "liftoff_overview": liftoff_overview,
                    "liftoff_details": liftoff_details,
                    "inspection_overview": inspection_overview,
                    "inspection_details": inspection_details,
                    "inspection_notes": inspection_notes,
                }
                db.add_recipe(name, description, json.dumps(payload, ensure_ascii=False))
                st.success("Receita salva.")

    st.write("### Receitas salvas")
    for r in db.list_recipes():
        with st.expander(f"#{r['id']} - {r['name']}"):
            st.write(r["description"] or "-")
            if st.button("Excluir receita", key=f"del_recipe_{r['id']}"):
                db.delete_recipe(r["id"])
                st.rerun()


def generate_tab():
    st.subheader("Gerar planilha")

    recipes = db.list_recipes()
    equipment = db.list_equipment()

    if not recipes:
        st.warning("Cadastre ao menos uma receita antes de gerar a planilha.")
        return

    c1, c2 = st.columns(2)
    recipe_id = c1.selectbox(
        "Receita",
        options=[r["id"] for r in recipes],
        format_func=lambda rid: next(r["name"] for r in recipes if r["id"] == rid),
    )
    equipment_id = c2.selectbox(
        "Equipamento",
        options=[0] + [e["id"] for e in equipment],
        format_func=lambda eid: "(nenhum)" if eid == 0 else next(e["name"] for e in equipment if e["id"] == eid),
    )

    template_path = st.text_input("Template XLSX", value=str(DEFAULT_TEMPLATE))
    filename = st.text_input("Nome do arquivo de saída", value=f"FP_gerada_{date.today().strftime('%Y%m%d')}.xlsx")

    if st.button("Gerar folha", type="primary"):
        template = Path(template_path)
        if not template.exists():
            st.error(f"Template não encontrado: {template}")
            return

        recipe = next(r for r in recipes if r["id"] == recipe_id)
        payload = json.loads(recipe["data_json"])

        # Enrich header with equipment info when selected.
        if equipment_id != 0:
            eq = next(e for e in equipment if e["id"] == equipment_id)
            enrich = f"Equipamento: {eq['name']} | Modelo: {eq['model'] or '-'} | Fabricante: {eq['manufacturer'] or '-'}"
            base_desc = payload.get("brief_desc", "")
            payload["brief_desc"] = f"{base_desc} | {enrich}" if base_desc else enrich

        output_path = OUTPUT_DIR / filename
        fill_sheet(template, output_path, payload)
        db.log_generated(recipe_id, equipment_id if equipment_id != 0 else None, output_path)

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
