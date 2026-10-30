"""Çalışan SQLite veritabanının tutarlı yedeği; var olan dosyanın üzerine yazmaz."""
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.engine import make_url

root = Path(__file__).resolve().parent.parent
url = make_url(os.environ.get('DATABASE_URL', f'sqlite:///{root / "backend/data/tgy.db"}'))
if url.get_backend_name() != 'sqlite':
    raise SystemExit('Bu yardımcı yalnızca SQLite içindir. PostgreSQL için pg_dump kullanın.')
source = Path(url.database).resolve()
if not source.is_file():
    raise SystemExit('Kaynak veritabanı bulunamadı. Önce uygulamayı başlatın.')
output = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'backend/data/backups' / (datetime.now(timezone.utc).strftime('tgy-%Y%m%d-%H%M%S-%f') + '.sqlite')
output = output.resolve()
output.parent.mkdir(parents=True, exist_ok=True)
# Özel oluşturma, yedek yolundaki mevcut dosyanın korunmasını sağlar.
with output.open('xb'):
    pass
try:
    with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as src, sqlite3.connect(output) as dest:
        src.backup(dest)
        if dest.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Yedek bütünlük kontrolü başarısız.')
except Exception:
    output.unlink(missing_ok=True)
    raise
print('Bütünlük kontrolünden geçen SQLite yedeği: ' + str(output))
