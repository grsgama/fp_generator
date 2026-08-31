from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import db
from xlsx_writer import fill_sheet

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATE_CANDIDATES = [
    BASE_DIR / "FP_FolhaDeProcesso_Modelo_EmBranco.xlsx",
    BASE_DIR.parent / "FP_FolhaDeProcesso_Modelo_EmBranco.xlsx",
    Path("/home/grsgama/Nextcloud2/LabNano/Folha de Processo/FP_FolhaDeProcesso_Modelo_EmBranco.xlsx"),
    Path("/home/grsgama/Nextcloud/LabNano/Folha de Processo/FP_FolhaDeProcesso_Modelo_EmBranco.xlsx"),
]
DEFAULT_TEMPLATE = next((p for p in TEMPLATE_CANDIDATES if p.exists()), TEMPLATE_CANDIDATES[0])

app = FastAPI(title="FP Generator", version="0.2.0")


def model_data(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class EquipmentIn(BaseModel):
    name: str = Field(min_length=1)
    category: str
    subtype: str
    model: str = ""
    manufacturer: str = ""
    location: str = ""
    status: str = "active"
    notes: str = ""


class RecipeParameterIn(BaseModel):
    name: str = Field(min_length=1)
    value: str = ""
    unit: str = ""


class RecipeBlockIn(BaseModel):
    name: str = Field(min_length=1)
    category: str
    subtype: str
    equipment_id: int
    author: str = ""
    confidence_level: str = "experimental"
    description: str = ""
    notes: str = ""
    parameters: list[RecipeParameterIn] = Field(default_factory=list)


class ProcessSheetBlockIn(BaseModel):
    recipe_block_id: int
    seq: int = 0
    title_override: str = ""
    notes_override: str = ""


class ProcessSheetIn(BaseModel):
    title: str = Field(min_length=1)
    author: str = ""
    project_name: str = ""
    supervisor: str = ""
    description: str = ""
    status: str = "draft"
    blocks: list[ProcessSheetBlockIn] = Field(default_factory=list)


@app.on_event("startup")
def startup() -> None:
    db.init_db()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    return {
        "categories": db.list_categories(),
        "sheet_statuses": ["draft", "review", "approved", "obsolete"],
        "recipe_statuses": ["experimental", "provisoria", "validada", "rotina", "obsoleta"],
        "default_template": str(DEFAULT_TEMPLATE),
        "template_exists": DEFAULT_TEMPLATE.exists(),
    }


@app.get("/api/equipment")
def list_equipment(include_inactive: bool = False) -> list[dict[str, Any]]:
    return db.list_equipment(include_inactive=include_inactive)


@app.post("/api/equipment")
def create_equipment(payload: EquipmentIn) -> dict[str, Any]:
    return db.create_equipment(model_data(payload))


@app.put("/api/equipment/{equipment_id}")
def update_equipment(equipment_id: int, payload: EquipmentIn) -> dict[str, Any]:
    if not db.get_equipment(equipment_id):
        raise HTTPException(status_code=404, detail="Equipment not found")
    updated = db.update_equipment(equipment_id, model_data(payload))
    return updated or {}


@app.delete("/api/equipment/{equipment_id}")
def delete_equipment(equipment_id: int) -> dict[str, Any]:
    if not db.get_equipment(equipment_id):
        raise HTTPException(status_code=404, detail="Equipment not found")
    removed = db.delete_equipment(equipment_id)
    return {
        "removed": removed,
        "message": "Equipment removed" if removed else "Equipment is used by recipes and was marked inactive",
    }


@app.get("/api/recipe-blocks")
def list_recipe_blocks() -> list[dict[str, Any]]:
    return db.list_recipe_blocks()


@app.post("/api/recipe-blocks")
def create_recipe_block(payload: RecipeBlockIn) -> dict[str, Any]:
    if not db.get_equipment(payload.equipment_id):
        raise HTTPException(status_code=400, detail="Equipment does not exist")
    return db.create_recipe_block(model_data(payload))


@app.put("/api/recipe-blocks/{recipe_block_id}")
def update_recipe_block(recipe_block_id: int, payload: RecipeBlockIn) -> dict[str, Any]:
    if not db.get_recipe_block(recipe_block_id):
        raise HTTPException(status_code=404, detail="Recipe block not found")
    if not db.get_equipment(payload.equipment_id):
        raise HTTPException(status_code=400, detail="Equipment does not exist")
    try:
        updated = db.update_recipe_block(recipe_block_id, model_data(payload))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return updated or {}


@app.delete("/api/recipe-blocks/{recipe_block_id}")
def delete_recipe_block(recipe_block_id: int) -> dict[str, Any]:
    if not db.get_recipe_block(recipe_block_id):
        raise HTTPException(status_code=404, detail="Recipe block not found")
    removed = db.delete_recipe_block(recipe_block_id)
    if not removed:
        raise HTTPException(status_code=400, detail="Recipe block is used by a process sheet")
    return {"removed": removed}


@app.post("/api/recipe-blocks/{recipe_block_id}/duplicate")
def duplicate_recipe_block(recipe_block_id: int) -> dict[str, Any]:
    duplicated = db.duplicate_recipe_block(recipe_block_id)
    if not duplicated:
        raise HTTPException(status_code=404, detail="Recipe block not found")
    return duplicated


@app.get("/api/process-sheets")
def list_process_sheets() -> list[dict[str, Any]]:
    return db.list_process_sheets()


@app.post("/api/process-sheets")
def create_process_sheet(payload: ProcessSheetIn) -> dict[str, Any]:
    return db.create_process_sheet(model_data(payload))


@app.put("/api/process-sheets/{process_sheet_id}")
def update_process_sheet(process_sheet_id: int, payload: ProcessSheetIn) -> dict[str, Any]:
    if not db.get_process_sheet(process_sheet_id):
        raise HTTPException(status_code=404, detail="Process sheet not found")
    try:
        updated = db.update_process_sheet(process_sheet_id, model_data(payload))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return updated or {}


@app.delete("/api/process-sheets/{process_sheet_id}")
def delete_process_sheet(process_sheet_id: int) -> dict[str, Any]:
    if not db.get_process_sheet(process_sheet_id):
        raise HTTPException(status_code=404, detail="Process sheet not found")
    try:
        db.delete_process_sheet(process_sheet_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"removed": True}


@app.post("/api/process-sheets/{process_sheet_id}/generate")
def generate_process_sheet(process_sheet_id: int) -> dict[str, Any]:
    sheet = db.get_process_sheet(process_sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Process sheet not found")
    if not sheet.get("blocks"):
        raise HTTPException(status_code=400, detail="Process sheet has no blocks")
    if not DEFAULT_TEMPLATE.exists():
        raise HTTPException(status_code=400, detail=f"Template not found: {DEFAULT_TEMPLATE}")

    safe_id = f"{process_sheet_id:04d}"
    filename = f"FP_{safe_id}_{date.today().strftime('%Y%m%d')}.xlsx"
    output_path = OUTPUT_DIR / filename
    fill_sheet(DEFAULT_TEMPLATE, output_path, db.sheet_to_xlsx_payload(sheet))
    generated = db.log_generated(process_sheet_id, output_path)
    return generated


@app.get("/api/generated")
def list_generated() -> list[dict[str, Any]]:
    return db.list_generated()


@app.get("/api/audit")
def list_audit(limit: int = 100) -> list[dict[str, Any]]:
    return db.list_audit_log(limit=limit)


@app.get("/api/recipe-blocks/{recipe_block_id}/revisions")
def list_recipe_block_revisions(recipe_block_id: int) -> list[dict[str, Any]]:
    if not db.get_recipe_block(recipe_block_id):
        raise HTTPException(status_code=404, detail="Recipe block not found")
    return db.list_recipe_block_revisions(recipe_block_id)


@app.get("/api/process-sheets/{process_sheet_id}/revisions")
def list_process_sheet_revisions(process_sheet_id: int) -> list[dict[str, Any]]:
    if not db.get_process_sheet(process_sheet_id):
        raise HTTPException(status_code=404, detail="Process sheet not found")
    return db.list_process_sheet_revisions(process_sheet_id)


@app.get("/download/{generated_id}")
def download_generated(generated_id: int) -> FileResponse:
    generated = next((item for item in db.list_generated() if item["id"] == generated_id), None)
    if not generated:
        raise HTTPException(status_code=404, detail="Generated file not found")
    path = Path(generated["output_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="File is missing on disk")
    return FileResponse(path, filename=path.name)


from PIL import Image


@app.post("/api/attachments/{entity_type}/{entity_id}")
async def upload_attachments(entity_type: str, entity_id: int, files: list[UploadFile] = File(...)):
    if entity_type not in {"equipment", "recipe_block"}:
        raise HTTPException(status_code=400, detail="entity_type invalido")
    if entity_type == "equipment" and not db.get_equipment(entity_id):
        raise HTTPException(status_code=404, detail="Equipamento nao encontrado")
    if entity_type == "recipe_block" and not db.get_recipe_block(entity_id):
        raise HTTPException(status_code=404, detail="Bloco de receita nao encontrado")

    saved = []
    for file in files:
        if not file.filename:
            continue
        ext = Path(file.filename).suffix
        stored_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = UPLOAD_DIR / stored_filename
        contents = await file.read()
        file_path.write_bytes(contents)
        file_type = file.content_type or "application/octet-stream"
        file_size = len(contents)

        if ext.lower() in {".tif", ".tiff"}:
            preview_path = UPLOAD_DIR / f"{stored_filename}.preview.png"
            try:
                with Image.open(file_path) as img:
                    img.seek(0)
                    img.convert("RGB").save(preview_path, format="PNG")
            except Exception:
                pass

        record = db.add_attachment(entity_type, entity_id, file.filename, stored_filename, str(file_path), file_type, file_size)
        saved.append(record)
    return saved


@app.get("/api/attachments/{entity_type}/{entity_id}")
def list_attachments(entity_type: str, entity_id: int) -> list[dict[str, Any]]:
    return db.list_attachments(entity_type, entity_id)


@app.delete("/api/attachments/{attachment_id}")
def delete_attachment(attachment_id: int):
    att = db.delete_attachment(attachment_id)
    if not att:
        raise HTTPException(status_code=404, detail="Anexo nao encontrado")
    path = Path(att["file_path"])
    if path.exists():
        try:
            path.unlink()
        except Exception:
            pass
    preview_path = UPLOAD_DIR / f"{att['stored_filename']}.preview.png"
    if preview_path.exists():
        try:
            preview_path.unlink()
        except Exception:
            pass
    return {"status": "ok", "deleted_id": attachment_id}


@app.get("/uploads/{filename}")
def serve_upload(filename: str) -> FileResponse:
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado")
    return FileResponse(path)


if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
