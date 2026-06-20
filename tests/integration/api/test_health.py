from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_root_returns_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]

def test_static_js_served():
    r = client.get("/static/app.js")
    assert r.status_code == 200

def test_static_css_served():
    r = client.get("/static/styles.css")
    assert r.status_code == 200
