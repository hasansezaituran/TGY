"""Python iş kuralları geliştirici testleri; bağımsız QA raporu değildir."""
from copy import deepcopy
import time
import unittest

from backend.rules import build_engine, delivery


def fixture():
    return {
        'orders': [{'id': 'o1', 'material': 'M1', 'name': 'Braket', 'project': 'P1', 'supplier': 'A', 'supplierName': 'A Firması', 'number': '45001', 'line': '10', 'qty': 100, 'received': 40, 'returned': 0, 'delivery': 'Kısmi', 'price': 5, 'deliveryOpen': 'Açık', 'requestOpen': 'Açık', 'status': 'Açık', 'approval': 'Onaylandı', 'currency': 'USD'}],
        'parts': [{'id': 'M1', 'old': 'ESK1', 'name': 'Braket', 'status': 'Aktif', 'mrp': 'Deniz', 'hours': 1, 'trim': .5}],
        'movements': [movement('m1', '2027-01-10', 'MERKEZ', 'DA')],
        'shipments': [], 'requirements': {'M1': ['K1']}, 'mappings': {'A': ['DA'], 'B': ['DB']}, 'links': {},
        'settings': {'returns': 'gross', 'molds': 'any', 'shipmentUnits': True, 'hoursUnit': 'piece'},
    }


def movement(id, date, source, target, ata='K1'):
    return {'id': id, 'material': 'M1', 'name': 'Braket', 'ata': ata, 'asy': 'ASY1', 'from': source, 'to': target, 'date': date, 'reason': 'Üretim'}


def shipment(id='s1'):
    return {'id': id, 'supplier': 'A', 'date': '2027-02-10', 'material': 'M1', 'name': 'Braket', 'serial': 'SN1', 'fai': 'Seri', 'trim': 'Trimli', 'order': '45001', 'note': 'IRS1'}


class RuleTests(unittest.TestCase):
    def assess(self, data):
        return build_engine(data).assess(data['orders'][0])

    def test_01_pasif_parca(self):
        data = fixture(); data['parts'][0]['status'] = 'Pasif'
        result = self.assess(data)
        self.assertEqual(result['state'], 'Üretilemez')
        self.assertIn('Parça üretim durumu pasif', result['reasons'])

    def test_02_yanlis_depo(self):
        data = fixture(); data['movements'][0]['to'] = 'DB'
        self.assertEqual(self.assess(data)['mold'], 'Kalıp uygun değil')
        self.assertEqual(self.assess(data)['state'], 'Üretilemez')

    def test_03_uygun_kalip_aktif_parca(self):
        self.assertEqual(self.assess(fixture())['state'], 'Üretilebilir')

    def test_04_eksik_kalip_kontrol_gerektirir(self):
        data = fixture(); data['movements'] = []
        self.assertEqual(self.assess(data)['state'], 'Kontrol gerekli')

    def test_05_transfer_iki_tedarikciyi_yeniden_hesaplar(self):
        data = fixture()
        data['orders'].append({**data['orders'][0], 'id': 'o2', 'line': '20', 'supplier': 'B'})
        before = build_engine(data)
        self.assertEqual(before.assess(data['orders'][0])['state'], 'Üretilebilir')
        data['movements'].append(movement('m2', '2027-02-20', 'DA', 'DB'))
        after = build_engine(data)
        self.assertEqual(after.assess(data['orders'][0])['state'], 'Üretilemez')
        self.assertEqual(after.assess(data['orders'][1])['state'], 'Üretilebilir')
        self.assertEqual(before.location('K1', 'M1')['place'], 'DA')

    def test_06_eksik_parca_uretilemez_sayilmaz(self):
        data = fixture(); data['parts'] = []
        result = self.assess(data)
        self.assertEqual(result['state'], 'Kontrol gerekli')
        self.assertIn('Parça kaydı eksik', result['reasons'])

    def test_07_mukerrer_seri_iki_satirda_uyari(self):
        data = fixture(); data['shipments'] = [shipment(), shipment('s2')]
        engine = build_engine(data)
        for item in data['shipments']:
            self.assertIn('Mükerrer seri numarası', engine.shipment_warnings(item))

    def test_08_sevkiyat_teslim_alim_degildir(self):
        data = fixture(); data['shipments'] = [shipment()]
        result = self.assess(data)
        self.assertEqual(len(result['shipments']), 1)
        self.assertEqual(result['net'], 40)
        self.assertEqual(data['orders'][0]['received'], 40)

    def test_09_belirsiz_eslesme_ve_gecerli_secim(self):
        data = fixture(); item = shipment(); data['shipments'] = [item]
        data['orders'].append({**data['orders'][0], 'id': 'o2', 'line': '20'})
        self.assertIsNone(build_engine(data).linked_order(item))
        self.assertIn('Belirsiz sipariş kalemi eşleşmesi', build_engine(data).shipment_warnings(item))
        data['links']['s1'] = 'o2'
        self.assertEqual(build_engine(data).linked_order(item)['id'], 'o2')
        data['links']['s1'] = 'gecersiz'
        self.assertIsNone(build_engine(data).linked_order(item))

    def test_10_parca_guncelleme_yeni_snapshot(self):
        data = fixture(); engine = build_engine(data)
        data['parts'][0]['status'] = 'Pasif'
        self.assertEqual(engine.assess(data['orders'][0])['state'], 'Üretilebilir')
        self.assertEqual(build_engine(data).assess(data['orders'][0])['state'], 'Üretilemez')

    def test_11_iade_kurallari_cift_dusum_yapmaz(self):
        data = fixture(); order = {**data['orders'][0], 'received': 120, 'qty': 120, 'returned': 5}
        self.assertEqual(delivery(order, data['settings'])['net'], 115)
        self.assertEqual(delivery(order, data['settings'])['remaining'], 5)
        self.assertEqual(delivery(order, {**data['settings'], 'returns': 'net'})['net'], 120)
        self.assertIsNone(delivery(order, {**data['settings'], 'returns': 'unknown'})['net'])

    def test_12_gecmis_tarihli_hareket_fiziksel_siradan_bagimsiz(self):
        data = fixture(); data['movements'] = [movement('m2', '2027-02-20', 'DA', 'DB'), *data['movements'], movement('m0', '2027-01-01', 'X', 'MERKEZ')]
        old_ids = [item['id'] for item in data['movements']]
        self.assertEqual(build_engine(data).location('K1', 'M1')['place'], 'DB')
        self.assertEqual([item['id'] for item in data['movements']], old_ids)

    def test_alternatif_bir_uygun_eksik_digerine_ragmen_yeterli(self):
        data = fixture(); data['requirements']['M1'] = ['K1', 'K2']
        self.assertEqual(self.assess(data)['state'], 'Üretilebilir')
        data['settings']['molds'] = 'all'
        self.assertEqual(self.assess(data)['state'], 'Kontrol gerekli')
        data['settings']['molds'] = 'unknown'
        self.assertEqual(self.assess(data)['state'], 'Kontrol gerekli')

    def test_tum_alternatifler_yanlissa_uretilemez(self):
        data = fixture(); data['requirements']['M1'] = ['K1', 'K2']
        data['movements'][0]['to'] = 'DB'
        data['movements'].append(movement('m2', '2027-01-10', 'MERKEZ', 'DB', 'K2'))
        self.assertEqual(self.assess(data)['state'], 'Üretilemez')

    def test_birden_fazla_olumsuz_neden_korunur(self):
        data = fixture(); data['parts'][0]['status'] = 'Pasif'; data['movements'][0]['to'] = 'DB'
        self.assertEqual(len(self.assess(data)['reasons']), 2)

    def test_ayni_tarih_kopuk_zincir_gecersiz_tarih_belirsizdir(self):
        for bad in [movement('m2', '2027-01-10', 'DA', 'DB'), movement('m2', '2027-02-10', 'X', 'DB')]:
            data = fixture(); data['movements'].append(bad)
            self.assertIsNone(build_engine(data).location('K1', 'M1')['place'])
        for invalid in ['tarih-yok', '2027-02-30', '2027-13-01']:
            data = fixture(); data['movements'][0]['date'] = invalid
            self.assertIsNone(build_engine(data).location('K1', 'M1')['place'])

    def test_eski_kod_isim_benzerligi_eslestirme_yapmaz(self):
        data = fixture(); data['orders'][0]['material'] = 'ESK1'
        self.assertEqual(self.assess(data)['part'], 'Veri eksik')
        data = fixture(); data['mappings'] = {}
        self.assertEqual(self.assess(data)['state'], 'Kontrol gerekli')

    def test_onay_fiziksel_uygunluktan_ayridir(self):
        data = fixture(); data['orders'][0]['approval'] = 'Bekliyor'
        result = self.assess(data)
        self.assertEqual(result['state'], 'Üretilebilir')
        self.assertTrue(any('Sipariş onayı bekleniyor' in item for item in result['warnings']))

    def test_ondalik_tutar_ve_miktar(self):
        data = fixture(); data['orders'][0].update(qty=.1, price=.2, received=.1, returned=.03)
        result = self.assess(data)
        self.assertEqual(result['total'], .02)
        self.assertEqual(result['net'], .07)
        self.assertEqual(result['remaining'], .03)

    def test_sifir_miktarda_yuzde_hesaplanmaz(self):
        data = fixture(); data['orders'][0]['qty'] = 0
        self.assertIsNone(self.assess(data)['percent'])

    def test_40_bin_sevkiyat_2_bin_siparis_tum_kayitlar(self):
        data = fixture(); base_order = data['orders'][0]; base_ship = shipment()
        data['orders'] = [{**base_order, 'id': f'o{i}', 'number': f'4500{i}', 'qty': 20, 'received': 20} for i in range(2000)]
        data['shipments'] = [{**base_ship, 'id': f's{i}', 'serial': f'SN{i}', 'order': data['orders'][i % 2000]['number']} for i in range(40000)]
        started = time.perf_counter(); engine = build_engine(data); indexed = time.perf_counter()
        matched = sum(engine.linked_order(item) is not None for item in data['shipments'])
        warnings = sum(len(engine.shipment_warnings(item)) for item in data['shipments'])
        results = [engine.assess(order) for order in data['orders']]
        elapsed = time.perf_counter() - started
        self.assertEqual(matched, 40000); self.assertEqual(warnings, 0)
        self.assertEqual(sum(len(item['shipments']) for item in results), 40000)
        self.assertTrue(all(item['state'] == 'Üretilebilir' and item['net'] == 20 and item['remaining'] == 0 for item in results))
        self.assertLess(elapsed, 10)
        print(f'Python sentetik hacim: 40000 sevkiyat / 2000 sipariş; indeks={(indexed-started)*1000:.0f}ms, toplam={elapsed*1000:.0f}ms')


if __name__ == '__main__':
    unittest.main()
