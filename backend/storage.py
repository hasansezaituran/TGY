"""SQLAlchemy depolama, iyimser eşzamanlılık ve işlem günlüğü."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import JSON, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint, create_engine, event, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from .models import MODELS, Settings

DEFAULT_DB = Path(__file__).resolve().parent / "data" / "tgy.db"
DEFAULT_DB.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB}")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 30} if DATABASE_URL.startswith("sqlite") else {}, pool_pre_ping=True)


@event.listens_for(engine, "connect")
def sqlite_integrity(dbapi_connection, connection_record):
    if engine.dialect.name == "sqlite":
        dbapi_connection.execute("PRAGMA foreign_keys=ON")


class Base(DeclarativeBase):
    pass


class Record(Base):
    __tablename__ = "source_records"
    __table_args__ = (UniqueConstraint("entity", "natural_key"),)
    entity: Mapped[str] = mapped_column(String(30), primary_key=True)
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    natural_key: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON)


class SourceColumns:
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    natural_key: Mapped[str] = mapped_column(Text, unique=True)
    payload: Mapped[dict] = mapped_column(JSON)


class OrderRecord(SourceColumns, Base):
    __tablename__ = "order_items"
    number: Mapped[str] = mapped_column(String(255), index=True)
    line: Mapped[str] = mapped_column(String(255))
    material: Mapped[str] = mapped_column(String(255), index=True)
    supplier: Mapped[str] = mapped_column(String(255), index=True)
    __table_args__ = (UniqueConstraint("number", "line"),)


class PartRecord(SourceColumns, Base):
    __tablename__ = "materials"


class MovementRecord(SourceColumns, Base):
    __tablename__ = "mold_movements"
    material: Mapped[str] = mapped_column(String(255), index=True)
    ata: Mapped[str] = mapped_column(String(255), index=True)
    date: Mapped[str] = mapped_column(String(10), index=True)


class ShipmentRecord(SourceColumns, Base):
    __tablename__ = "shipments"
    material: Mapped[str] = mapped_column(String(255), index=True)
    supplier: Mapped[str] = mapped_column(String(255), index=True)
    order: Mapped[str] = mapped_column(String(255), index=True)
    serial: Mapped[str] = mapped_column(String(255), index=True)
    date: Mapped[str] = mapped_column(String(10), index=True)


SOURCE_TABLES = {"orders": OrderRecord, "parts": PartRecord, "movements": MovementRecord, "shipments": ShipmentRecord}


class ShipmentOrderLink(Base):
    __tablename__ = "shipment_order_item_links"
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id"), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("order_items.id"), index=True)


def source_values(entity, value):
    columns = {"orders": ["number", "line", "material", "supplier"], "parts": [], "movements": ["material", "ata", "date"], "shipments": ["material", "supplier", "order", "serial", "date"]}
    return {"id": value["id"], "natural_key": natural_key(entity, value), "payload": value, **{key: value[key] for key in columns[entity]}}


class Revision(Base):
    __tablename__ = "state_revision"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[int] = mapped_column(Integer, default=0)


class ImportBatch(Base):
    __tablename__ = "import_batches"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="preview")
    staged: Mapped[dict] = mapped_column(JSON)
    report: Mapped[dict] = mapped_column(JSON)


class ImportSource(Base):
    """Doğrulama/normalizasyon öncesindeki özgün çalışma kitabının değişmez arşivi."""
    __tablename__ = "import_sources"
    batch_id: Mapped[str] = mapped_column(ForeignKey("import_batches.id"), primary_key=True)
    filename: Mapped[str] = mapped_column(Text)
    content: Mapped[bytes] = mapped_column(LargeBinary)


class Audit(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    revision: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[str] = mapped_column(String(40))
    action: Mapped[str] = mapped_column(String(40))
    details: Mapped[dict] = mapped_column(JSON)


def now():
    return datetime.now(timezone.utc).isoformat()


def initialize():
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        if session.get(Revision, 1) is None:
            session.add(Revision(id=1, value=0))


def natural_key(entity, value, record_id=None):
    fields = {"orders": ["number", "line"], "parts": ["id"], "movements": ["material", "ata", "asy", "date", "from", "to"], "shipments": ["serial", "supplier", "order", "date", "note"]}
    return json.dumps([value[f] for f in fields[entity]], ensure_ascii=False, separators=(",", ":")) if entity in fields else str(record_id)


def read_state(session):
    revision = session.get(Revision, 1).value
    data = {"orders": [], "parts": [], "movements": [], "shipments": [], "requirements": {}, "mappings": {}, "links": {}, "settings": Settings().model_dump()}
    for entity, table in SOURCE_TABLES.items():
        data[entity] = [record.payload for record in session.scalars(select(table).order_by(table.id))]
    for record in session.scalars(select(Record).order_by(Record.entity, Record.id)):
        if record.entity == "settings":
            data["settings"] = record.payload
        else:
            data[record.entity][record.id] = record.payload
    data["links"] = {link.shipment_id: link.order_id for link in session.scalars(select(ShipmentOrderLink))}
    return {"data": data, "revision": revision}


class StaleRevision(Exception):
    pass


def claim_revision(session, expected):
    result = session.execute(update(Revision).where(Revision.id == 1, Revision.value == expected).values(value=expected + 1))
    if result.rowcount != 1:
        raise StaleRevision("Veriler başka bir işlemde değişti. Yenileyip tekrar deneyin.")
    return expected + 1


def validate_value(entity, record_id, value):
    if entity in MODELS:
        result = MODELS[entity].model_validate(value).model_dump(by_alias=True)
        if record_id and record_id != result["id"]:
            raise ValueError("Kayıt kimliği kaynak kimliğiyle aynı olmalıdır")
        return result["id"], result
    if entity == "settings":
        return "default", Settings.model_validate(value).model_dump()
    if not isinstance(record_id, str) or not record_id.strip():
        raise ValueError("Eşleştirme anahtarı zorunludur")
    if entity in ("requirements", "mappings"):
        if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value) or len(value) != len(set(value)):
            raise ValueError("Eşleştirme değeri tekrarsız ve boş olmayan metin listesi olmalıdır")
    elif entity == "links" and (not isinstance(value, str) or not value.strip()):
        raise ValueError("Sevkiyat bağlantısı için sipariş kimliği zorunludur")
    return record_id, value


def audit(session, revision, action, details):
    session.add(Audit(revision=revision, created_at=now(), action=action, details=details))
