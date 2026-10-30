"""Sipariş, kalıp ve sevkiyat kuralları için istek kapsamlı indeksli motor.

Bir motor, girişin ayrı bir anlık görüntüsünü tutar. Veri değiştiğinde yeni motor
oluşturulur; süreç genelinde ya da istekler arasında paylaşılmış önbellek yoktur.
Dönen kayıtlar/sonuçlar salt okunur kabul edilmelidir. Kaynak veri değiştirilmez.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date
from decimal import Decimal
import re
from typing import Any

Record = dict[str, Any]
Key = tuple[str, str, str]


def _amount(value: Any) -> Decimal:
    """Ondalık hesapta ikili kayan nokta artıklarını büyütme."""
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _number(value: Decimal) -> int | float:
    """FastAPI/JSON ve TypeScript sözleşmesindeki sayısal alanları koru."""
    return int(value) if value == value.to_integral_value() else float(value)


def _order_key(record: Record, *, shipment: bool = False) -> Key:
    return (record['order' if shipment else 'number'], record['material'], record['supplier'])


def delivery(order: Record, settings: Record) -> Record:
    returned = _amount(order.get('returned', 0))
    if returned > 0 and settings.get('returns') == 'unknown':
        return {'net': None, 'remaining': None, 'percent': None}
    quantity = _amount(order['qty'])
    net = _amount(order.get('received', 0))
    if settings.get('returns') == 'gross':
        net -= returned
    return {
        'net': _number(net),
        'remaining': _number(quantity - net),
        'percent': _number(net / quantity * 100) if quantity > 0 else None,
    }


class RulesEngine:
    """Kuralları değiştirmeden toplu kayıtları indeksleyen bağımsız motor."""

    def __init__(self, data: Record):
        self.data = deepcopy(data)
        self.settings = self.data.get('settings', {})
        self._orders: dict[Key, list[Record]] = defaultdict(list)
        self._order_ids: dict[Key, dict[str, Record]] = defaultdict(dict)
        self._parts: dict[str, Record] = {}
        self._movements: dict[tuple[str, str], list[Record]] = defaultdict(list)
        self._linked: dict[str, list[Record]] = defaultdict(list)
        self._ambiguous: dict[Key, list[Record]] = defaultdict(list)
        self._locations: dict[tuple[str, str], Record] = {}
        self._warnings: dict[tuple[str, ...], list[str]] = {}
        self._serials = Counter(s.get('serial', '') for s in self.data.get('shipments', []))
        for order in self.data.get('orders', []):
            key = _order_key(order)
            self._orders[key].append(order)
            self._order_ids[key].setdefault(order['id'], order)
        for part in self.data.get('parts', []):
            self._parts.setdefault(part['id'], part)
        for movement in self.data.get('movements', []):
            self._movements[(movement['ata'], movement['material'])].append(movement)
        for shipment in self.data.get('shipments', []):
            linked = self.linked_order(shipment)
            if linked is not None:
                self._linked[linked['id']].append(shipment)
            elif self.candidates(shipment):
                self._ambiguous[_order_key(shipment, shipment=True)].append(shipment)

    def candidates(self, shipment: Record) -> list[Record]:
        return self._orders.get(_order_key(shipment, shipment=True), [])

    def linked_order(self, shipment: Record) -> Record | None:
        key = _order_key(shipment, shipment=True)
        orders = self._orders.get(key, [])
        selected = self._order_ids.get(key, {}).get(self.data.get('links', {}).get(shipment['id']))
        return selected if selected is not None else orders[0] if len(orders) == 1 else None

    def location(self, ata: str, material: str) -> Record:
        key = (ata, material)
        if key in self._locations:
            return self._locations[key]
        rows = sorted(self._movements.get(key, []), key=lambda row: row.get('date', ''))
        if not rows:
            result = {'place': None, 'reason': 'Kalıp hareketi / başlangıç konumu eksik', 'rows': rows}
        else:
            valid = True
            previous = None
            for row in rows:
                raw_date = row.get('date', '')
                try:
                    valid_date = bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', raw_date)) and date.fromisoformat(raw_date).isoformat() == raw_date
                except (TypeError, ValueError):
                    valid_date = False
                if not valid_date or not row.get('to') or (previous is not None and (raw_date == previous.get('date') or row.get('from') != previous.get('to'))):
                    valid = False
                    break
                previous = row
            result = {
                'place': rows[-1]['to'] if valid else None,
                'reason': 'Kronolojik hareket zinciri doğrulandı' if valid else 'Aynı tarihli veya zinciri çelişen kalıp hareketi',
                'rows': rows,
            }
        self._locations[key] = result
        return result

    def shipment_warnings(self, shipment: Record) -> list[str]:
        # İçerik anahtarı geçici çağrı nesnelerinin Python id yeniden kullanımından etkilenmez.
        identity = tuple(shipment.get(field, '') for field in ('id', 'supplier', 'material', 'order', 'serial', 'note'))
        cached = self._warnings.get(identity)
        if cached is not None:
            return cached
        orders = self.candidates(shipment)
        warnings: list[str] = []
        if not orders:
            warnings.append('Sipariş kaydı bulunamadı')
        selected_id = self.data.get('links', {}).get(shipment['id'])
        has_selected = selected_id in self._order_ids.get(_order_key(shipment, shipment=True), {})
        if len(orders) > 1 and not has_selected:
            warnings.append('Belirsiz sipariş kalemi eşleşmesi')
        serial = shipment.get('serial', '')
        if not serial:
            warnings.append('Seri numarası eksik')
        if serial and self._serials[serial] > 1:
            warnings.append('Mükerrer seri numarası')
        if not shipment.get('note'):
            warnings.append('İrsaliye numarası eksik')
        if self._parts.get(shipment['material'], {}).get('status') == 'Pasif':
            warnings.append('Pasif parçaya ait sevkiyat')
        self._warnings[identity] = warnings
        return warnings

    def assess(self, order: Record) -> Record:
        part = self._parts.get(order['material'])
        blocks: list[str] = []
        missing: list[str] = []
        if part is None:
            missing.append('Parça kaydı eksik')
        elif part.get('status') == 'Pasif':
            blocks.append('Parça üretim durumu pasif')
        elif part.get('status') != 'Aktif':
            missing.append('Parça üretim durumu bilinmiyor')
        required = self.data.get('requirements', {}).get(order['material'], [])
        mapped = self.data.get('mappings', {}).get(order['supplier'], [])
        mold = 'Belirlenemedi'
        if not required:
            missing.append('Gerekli kalıplar tanımlanmamış')
        elif not mapped:
            missing.append('Tedarikçi–depo eşleştirmesi eksik')
        else:
            locations = [self.location(ata, order['material']) for ata in required]
            suitable = sum(bool(item['place']) and item['place'] in mapped for item in locations)
            unsuitable = sum(bool(item['place']) and item['place'] not in mapped for item in locations)
            mode = self.settings.get('molds')
            if len(required) > 1 and mode == 'unknown':
                missing.append('Birden fazla kalıbın birlikte / alternatif kullanımı tanımlanmadı')
            elif (mode == 'any' and suitable > 0) or suitable == len(required):
                mold = 'Kalıp uygun'
            elif (unsuitable == len(required)) if mode == 'any' else (unsuitable > 0):
                mold = 'Kalıp uygun değil'
                blocks.append('Gerekli kalıp tedarikçide bulunmuyor')
            else:
                missing.append('Kalıp hareket geçmişi yetersiz veya çelişkili')
        reasons = blocks + missing
        state = 'Üretilemez' if blocks else 'Kontrol gerekli' if missing else 'Üretilebilir'
        shipments = self._linked.get(order['id'], [])
        ambiguous = self._ambiguous.get(_order_key(order), [])
        warnings = list(reasons)
        if order.get('approval') != 'Onaylandı':
            warnings.append('Sipariş onayı bekleniyor (fiziksel üretilebilirlikten bağımsız)')
        amounts = delivery(order, self.settings)
        if amounts['net'] is None:
            warnings.append('İade hesaplama kuralı tanımlanmadı')
        if amounts['net'] is not None and (amounts['net'] < 0 or amounts['net'] > order['qty']):
            warnings.append('Net teslimat miktarı sipariş sınırları dışında')
        if ambiguous:
            warnings.append('Belirsiz sevkiyat eşleşmesi')
        if len(shipments) > 1:
            warnings.append('Birden fazla sevkiyat kaydı')
        if any(self.shipment_warnings(shipment) for shipment in shipments):
            warnings.append('Sevkiyat kayıtlarında veri uyarısı')
        if self.settings.get('shipmentUnits') and amounts['net'] is not None and len(shipments) != amounts['net']:
            warnings.append('Sevk / teslim miktarı farklı; sevk teslim alım değildir')
        return {
            'state': state, 'mold': mold, 'part': part.get('status') if part is not None else 'Veri eksik',
            'reasons': reasons or ['Aktif parça ve gerekli kalıp konumu uygun'],
            'warnings': warnings, 'shipments': shipments, 'ambiguous': ambiguous,
            **amounts, 'total': _number(_amount(order['qty']) * _amount(order['price'])),
        }


def build_engine(data: Record) -> RulesEngine:
    return RulesEngine(data)
