from __future__ import annotations

from pathlib import Path

import pytest

from yaaf.loader import build_pattern, discover_routes


def test_build_pattern_static_and_dynamic() -> None:
    pattern, params, static_count, segment_count = build_pattern(["users", "[id]"] , prefix="api")
    assert params == ["id"]
    assert static_count == 1
    assert segment_count == 2
    assert pattern.startswith("^/api/")


def test_discover_routes_missing_dir(tmp_path: Path) -> None:
    routes, registry = discover_routes(str(tmp_path / "missing"))
    assert routes == []
    assert registry.by_type == {}
    assert registry.by_alias == {}


def test_discover_routes_dynamic_shadow_warning(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    base = tmp_path / "consumers" / "api"
    hello = base / "hello"
    dynamic = base / "[name]"
    hello.mkdir(parents=True)
    dynamic.mkdir(parents=True)

    (hello / "_service.py").write_text("class Service:...\nservice = Service()\n")
    (hello / "_server.py").write_text("async def get():...\n")
    (dynamic / "_service.py").write_text("class Service:...\nservice = Service()\n")
    (dynamic / "_server.py").write_text("async def get():...\n")

    discover_routes(str(tmp_path / "consumers"))
    captured = capsys.readouterr()
    assert "dynamic route /api/[name] matches static route /api/hello" in captured.out
