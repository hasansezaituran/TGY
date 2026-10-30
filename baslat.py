"""Yalnız Python ile TGY başlatma: python baslat.py (Windows: py baslat.py)."""
import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(command):
    subprocess.run(command, check=True, cwd=ROOT)


def available(port):
    with socket.socket() as sock:
        try:
            sock.bind(('127.0.0.1', port))
        except OSError as error:
            raise RuntimeError(f'{port} portu kullanımda. Önce bu porttaki uygulamayı kapatın veya TGY_PORT değişkenini başka bir porta ayarlayın.') from error


def ready(url, child):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for _ in range(150):
        if child.poll() is not None:
            raise RuntimeError('Servis başlatılamadı. Yukarıdaki hata mesajını kontrol edin.')
        try:
            with opener.open(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            pass
        time.sleep(.2)
    raise RuntimeError('Servis zamanında hazır olmadı. Yukarıdaki çıktıyı kontrol edin.')


def main():
    if sys.version_info < (3, 12):
        raise RuntimeError('Python 3.12 veya üzerini kurun. Python 3.12 ile doğrulandı.')
    if not (ROOT / 'dist/index.html').is_file():
        raise RuntimeError('Derlenmiş arayüz bulunamadı. ZIP dosyasının tamamını çıkarın; yalnız baslat.py dosyasını taşımayın.')
    try:
        port = int(os.environ.get('TGY_PORT', '8765'))
        if not 1024 <= port <= 65535:
            raise ValueError()
    except ValueError as error:
        raise RuntimeError('TGY_PORT, 1024 ile 65535 arasında bir sayı olmalıdır.') from error
    available(port)
    py = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not py.exists():
        print('Python ortamı hazırlanıyor…', flush=True)
        run([sys.executable, '-m', 'venv', str(ROOT / '.venv')])
    requirements = ROOT / 'backend/requirements-runtime.txt'
    marker = ROOT / '.venv/tgy-runtime.txt'
    expected = requirements.read_bytes()
    if not marker.exists() or marker.read_bytes() != expected:
        print('Python bağımlılıkları kuruluyor. İlk açılış internet bağlantısı gerektirir.', flush=True)
        run([str(py), '-m', 'pip', 'install', '-r', str(requirements)])
        marker.write_bytes(expected)
    child = None
    url = f'http://127.0.0.1:{port}'
    try:
        child = subprocess.Popen([str(py), '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT)
        ready(url + '/api/health', child)
        ready(url, child)
        print(f'\nTGY hazır: {url}', flush=True)
        print('Örneklerle denemek için sağ üstten “Demo · Geçici” seçin.', flush=True)
        print('Bu terminal açık kalsın. Durdurmak için Ctrl+C kullanın.\n', flush=True)
        if os.environ.get('TGY_NO_BROWSER') != '1':
            webbrowser.open(url)
        child.wait()
        if child.returncode not in (0, 130):
            raise RuntimeError('Servis durdu. Yukarıdaki çıktıyı kontrol edin.')
    except KeyboardInterrupt:
        print('\nTGY kapatılıyor. Kaydedilmiş gerçek veriler korunur.', flush=True)
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, OSError) as error:
        print(f'\nBaşlatma hatası: {error}', file=sys.stderr)
        sys.exit(1)
