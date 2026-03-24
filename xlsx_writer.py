from __future__ import annotations

from datetime import date
from pathlib import Path

from openpyxl import load_workbook


# Mapping of business fields to worksheet cells.
CELL_MAP = {
    "sheet_title": "E2",
    "supervisor": "E3",
    "project_name": "E4",
    "collab_type": "E5",
    "brief_desc": "E6",
    "approval_date": "E7",
    "substrate_overview": "D10",
    "substrate_details": "E10",
    "cleaning_overview": "D11",
    "cleaning_details": "E11",
    "resist1_overview": "D13",
    "resist1_details": "E13",
    "resist2_overview": "D14",
    "resist2_details": "E14",
    "exposure_overview": "D15",
    "exposure_details": "E15",
    "develop_overview": "D16",
    "develop_details": "E16",
    "deposition_overview": "D17",
    "deposition_details": "E17",
    "liftoff_overview": "D18",
    "liftoff_details": "E18",
    "inspection_overview": "D19",
    "inspection_details": "E19",
    "inspection_notes": "F19",
}


def _fmt_date(d: date | None):
    if d is None:
        return "---"
    return d.strftime("%d/%m/%Y")


def fill_sheet(template_path: Path, output_path: Path, payload: dict):
    wb = load_workbook(template_path)
    ws = wb[wb.sheetnames[0]]

    for key, cell in CELL_MAP.items():
        if key in payload:
            ws[cell] = payload.get(key, "")

    # If date was provided in a date widget.
    if isinstance(payload.get("approval_date"), date):
        ws[CELL_MAP["approval_date"]] = _fmt_date(payload["approval_date"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path
