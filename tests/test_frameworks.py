"""tests for the fastapi and flask adapters."""

from __future__ import annotations

import sys

import pytest


def _make_pkg(tmp_path, name, about):
    import json as _json
    pkg_dir = tmp_path / name
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "_about.json").write_text(_json.dumps(about))


def _cleanup(name):
    sys.modules.pop(name, None)


def test_fastapi_about_endpoint(tmp_path, monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from pathivu.frameworks.fastapi import about_router

    _make_pkg(tmp_path, "pathivu_fake_api", {"about": {"app_name": "api"}})
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        app = fastapi.FastAPI()
        app.include_router(about_router("pathivu_fake_api"))
        client = TestClient(app)

        r = client.get("/about")
        assert r.status_code == 200
        assert r.json() == {"about": {"app_name": "api"}}
    finally:
        _cleanup("pathivu_fake_api")


def test_fastapi_custom_path(tmp_path, monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from pathivu.frameworks.fastapi import about_router

    _make_pkg(tmp_path, "pathivu_fake_api2", {"x": 1})
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        app = fastapi.FastAPI()
        app.include_router(about_router("pathivu_fake_api2", path="/meta"))
        client = TestClient(app)

        assert client.get("/about").status_code == 404
        assert client.get("/meta").json() == {"x": 1}
    finally:
        _cleanup("pathivu_fake_api2")


def test_flask_about_endpoint(tmp_path, monkeypatch):
    flask = pytest.importorskip("flask")
    from pathivu.frameworks.flask import about_blueprint

    _make_pkg(tmp_path, "pathivu_fake_flask", {"about": {"app_name": "flask-api"}})
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        app = flask.Flask(__name__)
        app.register_blueprint(about_blueprint("pathivu_fake_flask"))
        client = app.test_client()

        r = client.get("/about")
        assert r.status_code == 200
        assert r.get_json() == {"about": {"app_name": "flask-api"}}
    finally:
        _cleanup("pathivu_fake_flask")


def test_flask_custom_path(tmp_path, monkeypatch):
    flask = pytest.importorskip("flask")
    from pathivu.frameworks.flask import about_blueprint

    _make_pkg(tmp_path, "pathivu_fake_flask2", {"y": 2})
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        app = flask.Flask(__name__)
        app.register_blueprint(about_blueprint("pathivu_fake_flask2", path="/meta", name="alt"))
        client = app.test_client()

        assert client.get("/about").status_code == 404
        assert client.get("/meta").get_json() == {"y": 2}
    finally:
        _cleanup("pathivu_fake_flask2")
