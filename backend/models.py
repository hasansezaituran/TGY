"""Kaynak kayıt sözleşmesi; hesaplanan alanlar bu modellere yazılamaz."""
from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

Number = Annotated[float, Field(strict=True, ge=0, allow_inf_nan=False)]
Text = StrictStr


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Text

    @field_validator("id")
    @classmethod
    def nonempty_id(cls, value):
        if not value.strip():
            raise ValueError("Kimlik boş olamaz")
        return value


class Order(Source):
    material: Text
    name: Text
    project: Text
    supplier: Text
    supplierName: Text
    number: Text
    line: Text
    qty: Number
    received: Number
    returned: Number
    delivery: Text
    price: Number
    deliveryOpen: Text
    requestOpen: Text
    status: Text
    approval: Text
    currency: Text = "USD"

    @field_validator("material", "supplier", "number", "line", "name", "currency")
    @classmethod
    def required_text(cls, value):
        if not value.strip():
            raise ValueError("Zorunlu alan boş olamaz")
        return value

    @field_validator("currency")
    @classmethod
    def currency_code(cls, value):
        if len(value) != 3 or not value.isascii() or not value.isalpha() or value != value.upper():
            raise ValueError("Para birimi üç büyük ASCII harfi olmalıdır")
        return value


class Part(Source):
    old: Text
    name: Text
    status: Literal["Aktif", "Pasif", "Bilinmiyor"]
    mrp: Text
    hours: Number
    trim: Number


class Movement(Source):
    material: Text
    name: Text
    ata: Text
    asy: Text
    from_: Text = Field(alias="from")
    to: Text
    date: Text
    reason: Text

    @field_validator("material", "ata", "from_", "to")
    @classmethod
    def required_text(cls, value):
        if not value.strip():
            raise ValueError("Zorunlu alan boş olamaz")
        return value

    @field_validator("date")
    @classmethod
    def valid_date(cls, value):
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError("Tarih YYYY-AA-GG biçiminde olmalıdır")
        return value


class Shipment(Source):
    supplier: Text
    date: Text
    material: Text
    name: Text
    serial: Text
    fai: Text
    trim: Text
    order: Text
    note: Text

    @field_validator("supplier", "material", "order")
    @classmethod
    def required_text(cls, value):
        if not value.strip():
            raise ValueError("Zorunlu alan boş olamaz")
        return value

    @field_validator("date")
    @classmethod
    def valid_date(cls, value):
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError("Tarih YYYY-AA-GG biçiminde olmalıdır")
        return value


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    returns: Literal["gross", "net", "unknown"] = "gross"
    molds: Literal["any", "all", "unknown"] = "any"
    shipmentUnits: bool = Field(default=True, strict=True)
    hoursUnit: Literal["piece", "batch", "unknown"] = "piece"


MODELS = {"orders": Order, "parts": Part, "movements": Movement, "shipments": Shipment}


class Change(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entity: Literal["orders", "parts", "movements", "shipments", "requirements", "mappings", "links", "settings"]
    id: Text | None = None
    value: dict | list[StrictStr] | StrictStr


class Changes(BaseModel):
    expected_revision: int = Field(ge=0, strict=True)
    changes: list[Change] = Field(max_length=100000)


class Commit(BaseModel):
    expected_revision: int = Field(ge=0, strict=True)
    update_existing: bool = Field(default=False, strict=True)
