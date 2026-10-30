"""Node gerektirmeyen dağıtımda aynı Python sunucusunun HTML/API sunması."""
import importlib
from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.styles = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and attrs.get('src'):
            self.scripts.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') == 'stylesheet' and attrs.get('href'):
            self.styles.append(attrs['href'])


@pytest.fixture
def distributed_client(tmp_path, monkeypatch):
    storage = importlib.import_module('backend.storage')
    api = importlib.import_module('backend.main')
    engine = create_engine(f'sqlite:///{tmp_path / "distribution.db"}', connect_args={'check_same_thread': False})
    monkeypatch.setattr(storage, 'engine', engine)
    with TestClient(api.app) as client:
        yield client
    engine.dispose()


def test_root_serves_built_turkish_application(distributed_client):
    response = distributed_client.get('/')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/html')
    assert '<html lang="tr">' in response.text
    assert '<div id="root"></div>' in response.text
    assert 'TGY' in response.text
    assert response.content == (Path(__file__).resolve().parents[2] / 'dist' / 'index.html').read_bytes()


def test_referenced_javascript_and_stylesheet_are_served(distributed_client):
    parser = AssetParser()
    parser.feed(distributed_client.get('/').text)
    assert parser.scripts, 'Derlenmiş uygulamanın JavaScript giriş dosyası bulunmalı'
    assert parser.styles, 'Derlenmiş uygulamanın CSS dosyası bulunmalı'
    for path in parser.scripts + parser.styles:
        assert path.startswith('/assets/'), path
        response = distributed_client.get(path)
        assert response.status_code == 200, path
        assert len(response.content) > 100, path
        assert not response.headers['content-type'].startswith('text/html'), path


def test_api_routes_have_priority_over_static_mount(distributed_client):
    response = distributed_client.get('/api/health')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('application/json')
    assert response.json()['status'] == 'ok'
    assert response.json()['database'] == 'sqlite'


def test_distribution_starts_with_empty_real_sources(distributed_client):
    response = distributed_client.get('/api/state')
    assert response.status_code == 200
    value = response.json()
    assert value['revision'] == 0
    assert all(value['data'][entity] == [] for entity in ('orders', 'parts', 'movements', 'shipments'))
    assert value['data']['settings']['returns'] == 'gross'


def test_api_documentation_remains_available(distributed_client):
    response = distributed_client.get('/docs')
    assert response.status_code == 200
    assert 'swagger-ui' in response.text
    schema = distributed_client.get('/openapi.json')
    assert schema.status_code == 200
    assert '/api/imports/preview' in schema.json()['paths']


def test_unknown_paths_are_404_and_sources_are_not_published(distributed_client):
    for path in ('/olmayan-sayfa', '/assets/olmayan.js', '/backend/storage.py', '/backend/data/tgy.db'):
        response = distributed_client.get(path)
        assert response.status_code == 404, (path, response.status_code)
