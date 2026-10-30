"""TGY REST API. Çalıştırma: uvicorn backend.main:app --host 127.0.0.1 --port 8000"""
import io
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool
from pydantic import ValidationError
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from . import storage
from .imports import MAX_BYTES, WorkbookError, make_workbook, preview
from .models import Changes, Commit, MODELS
from .storage import Audit, ImportBatch, ImportSource, Record, SOURCE_TABLES, ShipmentOrderLink, StaleRevision, audit, claim_revision, natural_key, now, read_state, source_values, validate_value


@asynccontextmanager
async def lifespan(app):
    storage.initialize()
    yield


app = FastAPI(title="TGY Sipariş ve Sevkiyat API", version="1.0.0", lifespan=lifespan)


def validate_links(data):
    """Kaynak güncellemesi mevcut kesin bağlantıları da geçersiz kılamaz."""
    orders = {row["id"]: row for row in data["orders"]}
    shipments = {row["id"]: row for row in data["shipments"]}
    for shipment_id, order_id in data["links"].items():
        source, target = shipments.get(shipment_id), orders.get(order_id)
        if not source or not target or (source["order"], source["material"], source["supplier"]) != (target["number"], target["material"], target["supplier"]):
            raise HTTPException(422, "Sevkiyat bağlantısı geçerli sipariş adaylarından birine yapılmalıdır")


@app.exception_handler(StaleRevision)
async def stale_handler(request, error):
    return JSONResponse(status_code=409, content={"detail": str(error)})


@app.exception_handler(IntegrityError)
async def integrity_handler(request, error):
    return JSONResponse(status_code=409, content={"detail": "Kayıt kimliği veya doğal anahtar başka bir kayıtta kullanılıyor. İşlem geri alındı."})


@app.exception_handler(ValidationError)
async def validation_handler(request, error):
    return JSONResponse(status_code=422, content={"detail": [{"field": ".".join(map(str, item["loc"])), "message": item["msg"]} for item in error.errors()]})


@app.get("/api/health")
def health():
    with Session(storage.engine) as session:
        revision = session.get(storage.Revision, 1)
        return {"status": "ok", "revision": revision.value, "database": storage.engine.dialect.name}


@app.get("/api/state")
def state():
    with Session(storage.engine) as session:
        return read_state(session)


@app.post("/api/changes")
def changes(body: Changes):
    with Session(storage.engine) as session, session.begin():
        revision = claim_revision(session, body.expected_revision)
        for change in body.changes:
            try:
                record_id, value = validate_value(change.entity, change.id, change.value)
            except ValueError as error:
                raise HTTPException(422, str(error)) from error
            if change.entity in MODELS:
                table = SOURCE_TABLES[change.entity]
                record = session.get(table, record_id)
                before = record.payload if record else None
                values = source_values(change.entity, value)
                if record:
                    for key, val in values.items():
                        setattr(record, key, val)
                else:
                    session.add(table(**values))
            elif change.entity == "links":
                record = session.get(ShipmentOrderLink, record_id)
                before = record.order_id if record else None
                if record:
                    record.order_id = value
                else:
                    session.add(ShipmentOrderLink(shipment_id=record_id, order_id=value))
            else:
                record = session.get(Record, (change.entity, record_id))
                before = record.payload if record else None
                if record:
                    record.payload = value
                else:
                    session.add(Record(entity=change.entity, id=record_id, natural_key=record_id, payload=value))
            audit(session, revision, "kaynak_guncelleme", {"entity": change.entity, "id": record_id, "before": before, "after": value})
        session.flush()
        current = read_state(session)
        # Eksik kaynak kayıtları alınabilir; kesin bağlantılar ise geçerli aday olmalıdır.
        validate_links(current["data"])
        return current


@app.get("/api/orders")
def orders(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500), q: str = Query("", max_length=300)):
    from .rules import build_engine
    with Session(storage.engine) as session:
        current = read_state(session)
    data = current["data"]
    engine = build_engine(data)
    query = q.casefold()
    filtered = [row for row in data["orders"] if not query or any(query in str(value).casefold() for value in row.values())]
    selected = filtered[(page - 1) * page_size:page * page_size]
    return {"items": [{**row, "computed": engine.assess(row)} for row in selected], "total": len(filtered), "page": page, "page_size": page_size, "revision": current["revision"]}


@app.get("/api/assessments")
def assessments():
    from .rules import build_engine
    with Session(storage.engine) as session:
        current = read_state(session)
    data = current["data"]
    engine = build_engine(data)
    items = {}
    for order in data["orders"]:
        assessed = engine.assess(order)
        items[order["id"]] = {**assessed, "shipments": [row["id"] for row in assessed["shipments"]], "ambiguous": [row["id"] for row in assessed["ambiguous"]]}
    return {"revision": current["revision"], "items": items}


def xlsx_response(content, name):
    return StreamingResponse(io.BytesIO(content), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="{name}.xlsx"'})


@app.get("/api/export")
def export():
    with Session(storage.engine) as session:
        current = read_state(session)
    return xlsx_response(make_workbook(current["data"]), "TGY-kaynak-veriler")


@app.get("/api/template")
def template():
    return xlsx_response(make_workbook(), "TGY-sablon")


@app.post("/api/imports/preview")
async def import_preview(file: UploadFile = File(...), kind: str = Form("auto")):
    if kind not in {"auto", *MODELS}:
        raise HTTPException(422, "Geçersiz liste türü")
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(422, "Yalnızca .xlsx dosyaları desteklenir")
    content = await file.read(MAX_BYTES + 1)
    await file.close()
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "Dosya en fazla 16 MB olabilir")
    # Büyük Excel ayrıştırması sunucunun olay döngüsünü ve health isteklerini kilitlemez.
    return await run_in_threadpool(persist_preview, content, kind, file.filename)


def persist_preview(content, kind, filename="kaynak.xlsx"):
    with Session(storage.engine) as session:
        current = read_state(session)
        try:
            report, staged = preview(content, kind, current)
        except WorkbookError as error:
            raise HTTPException(422, str(error)) from error
        session.add(ImportBatch(id=report["id"], revision=current["revision"], created_at=now(), status="preview", staged=staged, report=report))
        session.flush()
        session.add(ImportSource(batch_id=report["id"], filename=filename, content=content))
        session.commit()
    return report


@app.get("/api/imports/{batch_id}/source")
def import_source(batch_id: str):
    with Session(storage.engine) as session:
        source = session.get(ImportSource, batch_id)
        if source is None:
            raise HTTPException(404, "Aktarımın özgün kaynak dosyası bulunamadı")
        # Kullanıcı dosya adı HTTP başlığına yerleştirilmez.
        return xlsx_response(source.content, "TGY-kaynak")


@app.post("/api/imports/{batch_id}/commit")
def import_commit(batch_id: str, body: Commit):
    with Session(storage.engine) as session, session.begin():
        batch = session.get(ImportBatch, batch_id)
        if batch is None:
            raise HTTPException(404, "Aktarım önizlemesi bulunamadı")
        if batch.status != "preview":
            raise HTTPException(409, "Bu aktarım daha önce uygulandı")
        if not batch.report["can_commit"]:
            raise HTTPException(422, "Hatalı önizleme uygulanamaz")
        if body.expected_revision != batch.revision:
            raise StaleRevision("Önizlemenin sürümü değişti. Dosyayı yeniden önizleyin.")
        revision = claim_revision(session, body.expected_revision)
        result = {"inserted": 0, "updated": 0, "preserved": 0, "identical": 0}
        for entity, rows in batch.staged.items():
            table = SOURCE_TABLES[entity]
            existing = {record.natural_key: record for record in session.scalars(select(table))}
            additions = []
            for raw in rows:
                value = MODELS[entity].model_validate(raw).model_dump(by_alias=True)
                key = natural_key(entity, value)
                old = existing.get(key)
                if old:
                    value["id"] = old.id
                    if old.payload == value:
                        result["identical"] += 1
                    elif body.update_existing:
                        before = old.payload
                        for name, val in source_values(entity, value).items():
                            setattr(old, name, val)
                        audit(session, revision, "aktarim_guncelleme", {"batch": batch_id, "entity": entity, "id": old.id, "before": before, "after": value})
                        result["updated"] += 1
                    else:
                        result["preserved"] += 1
                else:
                    additions.append(source_values(entity, value))
                    result["inserted"] += 1
            # SQLAlchemy executemany; 40.000 satırı ORM nesnesi olarak tek tek eklemez.
            for offset in range(0, len(additions), 1000):
                session.execute(insert(table), additions[offset:offset + 1000])
        batch.status = "committed"
        audit(session, revision, "excel_aktarim", {"batch": batch_id, "update_existing": body.update_existing, **result})
        session.flush()
        validate_links(read_state(session)["data"])
        return {"id": batch_id, "revision": revision, **result}


@app.get("/api/audit")
def audit_history(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    with Session(storage.engine) as session:
        rows = session.scalars(select(Audit).order_by(Audit.id.desc()).offset((page - 1) * page_size).limit(page_size))
        return {"items": [{"id": row.id, "revision": row.revision, "created_at": row.created_at, "action": row.action, "details": row.details} for row in rows], "page": page}

# Derlenmiş web arayüzünü aynı Python sunucusundan sun; son sırada kalmalı.
# Böylece /api ve /docs istekleri kendi uç noktalarına ulaşır.
from pathlib import Path
from fastapi.staticfiles import StaticFiles

_web_directory = Path(__file__).resolve().parent.parent / "dist"
if (_web_directory / "index.html").is_file():
    app.mount("/", StaticFiles(directory=str(_web_directory), html=True), name="web")
