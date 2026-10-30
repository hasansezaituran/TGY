"""Kaynak ve derlenmiş arayüzü içeren, platformdan bağımsız dağıtım ZIP'i."""
import sys
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent.parent
output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root / 'release/TGY-Python.zip'
if not (root / 'dist/index.html').is_file():
    raise SystemExit('Derlenmiş arayüz eksik. Geliştirme makinesinde npm run build çalıştırın.')
excluded = {'.git', '.venv', 'node_modules', '__pycache__', '.pytest_cache', 'test-results', 'playwright-report', 'release'}
output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
    for source in sorted(root.rglob('*')):
        relative = source.relative_to(root)
        if not source.is_file() or source.resolve() == output:
            continue
        if any(part in excluded for part in relative.parts) or relative.parts[:2] == ('backend', 'data'):
            continue
        if source.name in {'.env', 'tsconfig.tsbuildinfo'} or source.suffix in {'.pyc', '.db', '.sqlite'}:
            continue
        archive.write(source, Path('TGY') / relative)
with zipfile.ZipFile(output) as archive:
    if archive.testzip() is not None:
        raise SystemExit('ZIP bütünlük kontrolü başarısız.')
    for required in ('TGY/baslat.py', 'TGY/dist/index.html', 'TGY/backend/requirements-runtime.txt', 'TGY/BASLAT.bat'):
        assert required in archive.namelist(), required
    print(f'Paket hazır: {output} ({len(archive.namelist())} dosya, {output.stat().st_size:,} bayt)')
