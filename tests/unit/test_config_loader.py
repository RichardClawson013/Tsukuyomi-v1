"""Config loader — validation and extends-merge."""
import json
from pathlib import Path

import pytest

from tsukuyomi.core.config import load_config


def test_load_minimal(tmp_path: Path):
    cfg_path = tmp_path / "c.json"
    cfg_path.write_text(json.dumps({"schema_version": 1}))
    cfg = load_config(cfg_path)
    assert cfg.schema_version == 1
    assert cfg.interceptor.port == 9999


def test_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "does_not_exist.json")


def test_invalid_json(tmp_path: Path):
    p = tmp_path / "c.json"
    p.write_text("{ not valid json")
    with pytest.raises(ValueError, match="invalid JSON"):
        load_config(p)


def test_extends_merges(tmp_path: Path):
    parent = tmp_path / "base.json"
    parent.write_text(json.dumps({"schema_version": 1, "interceptor": {"port": 8888}}))
    child = tmp_path / "child.json"
    child.write_text(json.dumps({
        "extends": "base.json",
        "interceptor": {"host": "0.0.0.0"}
    }))
    cfg = load_config(child)
    assert cfg.interceptor.port == 8888
    assert cfg.interceptor.host == "0.0.0.0"
