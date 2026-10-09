import json

import pytest

from app.lib import cells


def write_cells_config(tmp_path, cells_section=None):
    if cells_section is None:
        cells_section = {
            "endpoint": "https://file.b4m.jp/dav/workspace/",
            "username": "user",
            "password": "pass",
            "upload_folder": "Scans/",
            "delete_after_upload": False,
        }
    data = {"provider": "cells", "cells": cells_section}
    cfg = tmp_path / "upload.json"
    cfg.write_text(json.dumps(data), encoding="utf-8")
    return cfg


def test_load_cells_config_ok(tmp_path):
    cfg_path = write_cells_config(tmp_path)

    cfg = cells.load_cells_config(str(cfg_path))
    assert cfg["endpoint"].startswith("https://file.b4m.jp/dav/")
    assert cfg["upload_folder"] == "Scans/"


def test_load_cells_config_invalid_section(tmp_path):
    cfg_path = tmp_path / "upload.json"
    cfg_path.write_text(json.dumps({"provider": "cells", "cells": "oops"}), encoding="utf-8")

    with pytest.raises(ValueError):
        cells.load_cells_config(str(cfg_path))


def test_load_cells_config_missing_section(tmp_path):
    cfg_path = tmp_path / "upload.json"
    cfg_path.write_text(json.dumps({"provider": "cells"}), encoding="utf-8")

    with pytest.raises(ValueError):
        cells.load_cells_config(str(cfg_path))


@pytest.mark.parametrize("status_stdout,expected", [
    ("HTTP/1.1 201 Created\n", True),
    ("HTTP/1.1 405 Method Not Allowed\n", True),
    ("HTTP/1.1 409 Conflict\n", True),
    ("HTTP/1.1 401 Unauthorized\n", False),
    ("HTTP/1.1 500 Internal Server Error\n", False),
    ("", False),
])
def test_create_remote_directory_status_codes(monkeypatch, status_stdout, expected):
    cfg = {
        "endpoint": "https://file.b4m.jp/dav/workspace/",
        "username": "user",
        "password": "pass",
    }

    class DummyResult:
        def __init__(self, stdout):
            self.stdout = stdout
            self.stderr = ""

    monkeypatch.setattr(cells, "load_cells_config", lambda: cfg)
    monkeypatch.setattr(
        cells.subprocess,
        "run",
        lambda *a, **k: DummyResult(status_stdout),
    )

    assert cells.create_remote_directory("Scans/dir/") is expected


def test_upload_file_to_cells_success(monkeypatch, tmp_path):
    cfg = {
        "endpoint": "https://file.b4m.jp/dav/workspace/",
        "username": "user",
        "password": "pass",
        "upload_folder": "Scans/",
    }

    class DummyResult:
        def __init__(self):
            self.stdout = "HTTP/1.1 201 Created\n"
            self.stderr = ""
            self.returncode = 0

    file_path = tmp_path / "test.txt"
    file_path.write_text("hello", encoding="utf-8")

    monkeypatch.setattr(cells, "load_cells_config", lambda: cfg)
    monkeypatch.setattr(cells.subprocess, "run", lambda *a, **k: DummyResult())

    assert cells.upload_file_to_cells(str(file_path)) is True


def test_upload_file_to_cells_missing_file(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        cells,
        "load_cells_config",
        lambda: {
            "endpoint": "https://file.b4m.jp/dav/workspace/",
            "username": "user",
            "password": "pass",
            "upload_folder": "Scans/",
        },
    )

    ok = cells.upload_file_to_cells(str(tmp_path / "no.txt"))
    captured = capsys.readouterr()
    assert ok is False
    assert "not found" in captured.out


def test_upload_file_to_cells_http_error(monkeypatch, tmp_path):
    cfg = {
        "endpoint": "https://file.b4m.jp/dav/workspace/",
        "username": "user",
        "password": "pass",
        "upload_folder": "Scans/",
    }

    class DummyResult:
        def __init__(self):
            self.stdout = "HTTP/1.1 403 Forbidden\n"
            self.stderr = ""
            self.returncode = 0

    file_path = tmp_path / "test.txt"
    file_path.write_text("hello", encoding="utf-8")

    monkeypatch.setattr(cells, "load_cells_config", lambda: cfg)
    monkeypatch.setattr(cells.subprocess, "run", lambda *a, **k: DummyResult())

    assert cells.upload_file_to_cells(str(file_path)) is False


def test_upload_directory_to_cells_basic(monkeypatch, tmp_path):
    local_dir = tmp_path / "scan"
    local_dir.mkdir()
    (local_dir / "a.jpg").write_text("a", encoding="utf-8")
    (local_dir / "b.jpg").write_text("b", encoding="utf-8")

    cfg = {
        "endpoint": "https://file.b4m.jp/dav/workspace/",
        "username": "user",
        "password": "pass",
        "upload_folder": "Scans/",
        "delete_after_upload": False,
    }

    uploaded = []

    monkeypatch.setattr(cells, "load_cells_config", lambda: cfg)
    monkeypatch.setattr(cells, "create_remote_directory", lambda remote_dir: True)
    monkeypatch.setattr(
        cells,
        "upload_file_to_cells",
        lambda file_path, remote_path=None: uploaded.append((file_path, remote_path)) or True,
    )

    ok = cells.upload_directory_to_cells(str(local_dir), delete_after_upload=False)
    assert ok is True
    assert len(uploaded) == 2


def test_upload_directory_to_cells_create_remote_dir_fail(monkeypatch, tmp_path):
    local_dir = tmp_path / "scan"
    local_dir.mkdir()
    (local_dir / "a.jpg").write_text("a", encoding="utf-8")

    monkeypatch.setattr(
        cells,
        "load_cells_config",
        lambda: {
            "endpoint": "https://file.b4m.jp/dav/workspace/",
            "username": "user",
            "password": "pass",
            "upload_folder": "Scans/",
            "delete_after_upload": False,
        },
    )
    monkeypatch.setattr(cells, "create_remote_directory", lambda remote: False)

    assert cells.upload_directory_to_cells(str(local_dir)) is False


def test_upload_directory_to_cells_no_files(monkeypatch, tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    monkeypatch.setattr(
        cells,
        "load_cells_config",
        lambda: {
            "endpoint": "https://file.b4m.jp/dav/workspace/",
            "username": "user",
            "password": "pass",
            "upload_folder": "Scans/",
            "delete_after_upload": False,
        },
    )
    monkeypatch.setattr(cells, "create_remote_directory", lambda remote: True)

    assert cells.upload_directory_to_cells(str(empty_dir)) is False


def test_upload_pdf_to_cells_success(monkeypatch, tmp_path):
    cfg = {
        "endpoint": "https://file.b4m.jp/dav/workspace/",
        "username": "user",
        "password": "pass",
        "upload_folder": "Scans/",
        "delete_after_upload": False,
    }

    class DummyResult:
        def __init__(self):
            self.stdout = "HTTP/1.1 201 Created\n"
            self.stderr = ""
            self.returncode = 0

    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy")

    monkeypatch.setattr(cells, "load_cells_config", lambda: cfg)
    monkeypatch.setattr(cells.subprocess, "run", lambda *a, **k: DummyResult())

    assert cells.upload_pdf_to_cells(str(pdf), delete_after_upload=False) is True


def test_upload_pdf_to_cells_delete_after(monkeypatch, tmp_path):
    cfg = {
        "endpoint": "https://file.b4m.jp/dav/workspace/",
        "username": "user",
        "password": "pass",
        "upload_folder": "Scans/",
        "delete_after_upload": True,
    }

    class DummyResult:
        def __init__(self):
            self.stdout = "HTTP/1.1 201 Created\n"
            self.stderr = ""
            self.returncode = 0

    pdf = tmp_path / "doc2.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy")

    monkeypatch.setattr(cells, "load_cells_config", lambda: cfg)
    monkeypatch.setattr(cells.subprocess, "run", lambda *a, **k: DummyResult())

    ok = cells.upload_pdf_to_cells(str(pdf), delete_after_upload=True)
    assert ok is True
    assert not pdf.exists()


def test_upload_pdf_to_cells_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        cells,
        "load_cells_config",
        lambda: {
            "endpoint": "https://file.b4m.jp/dav/workspace/",
            "username": "user",
            "password": "pass",
            "upload_folder": "Scans/",
            "delete_after_upload": False,
        },
    )

    assert cells.upload_pdf_to_cells(str(tmp_path / "no.pdf")) is False


def test_test_cells_connection_ok(monkeypatch):
    class DummyResult:
        def __init__(self):
            self.stdout = "HTTP/1.1 200 OK\n"
            self.stderr = ""
            self.returncode = 0

    monkeypatch.setattr(
        cells,
        "load_cells_config",
        lambda: {
            "endpoint": "https://file.b4m.jp/dav/workspace/",
            "username": "user",
            "password": "pass",
        },
    )
    monkeypatch.setattr(cells.subprocess, "run", lambda *a, **k: DummyResult())

    assert cells.test_cells_connection() is True


def test_test_cells_connection_error_status(monkeypatch):
    class DummyResult:
        def __init__(self):
            self.stdout = "HTTP/1.1 500 Internal Server Error\n"
            self.stderr = ""
            self.returncode = 0

    monkeypatch.setattr(
        cells,
        "load_cells_config",
        lambda: {
            "endpoint": "https://file.b4m.jp/dav/workspace/",
            "username": "user",
            "password": "pass",
        },
    )
    monkeypatch.setattr(cells.subprocess, "run", lambda *a, **k: DummyResult())

    assert cells.test_cells_connection() is False


def test_test_cells_connection_no_status_line(monkeypatch):
    class DummyResult:
        def __init__(self):
            self.stdout = ""
            self.stderr = ""
            self.returncode = 0

    monkeypatch.setattr(
        cells,
        "load_cells_config",
        lambda: {
            "endpoint": "https://file.b4m.jp/dav/workspace/",
            "username": "user",
            "password": "pass",
        },
    )
    monkeypatch.setattr(cells.subprocess, "run", lambda *a, **k: DummyResult())

    assert cells.test_cells_connection() is False
