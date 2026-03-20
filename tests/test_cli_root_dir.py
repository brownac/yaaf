"""Test CLI functionality with custom root directory."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from yaaf.cli import main


def test_cli_serve_with_default_app_uses_custom_root(tmp_path: Path) -> None:
    """Test that serve command with default app uses custom root directory."""
    custom_root = tmp_path / "my_root"
    route_dir = custom_root / "hello"
    route_dir.mkdir(parents=True)

    (route_dir / "_service.py").write_text("class Service: pass\nservice = Service()")
    (route_dir / "_server.py").write_text("async def get(): return 'Hello'")

    with patch("yaaf.cli.uvicorn.run") as mock_run:
        with patch.object(
            sys,
            "argv",
            ["yaaf", "--root", str(custom_root), "--port", "8001"],
        ):
            try:
                main()
            except SystemExit:
                pass

    assert mock_run.called
    app_instance = mock_run.call_args[0][0]
    assert app_instance._root_dir == str(custom_root)


def test_cli_serve_with_custom_app_path(tmp_path: Path) -> None:
    """Test that serve command with custom app path works correctly."""
    custom_app_dir = tmp_path / "custom_app"
    custom_app_dir.mkdir()

    (custom_app_dir / "__init__.py").write_text("")
    (custom_app_dir / "app.py").write_text("""
from yaaf.app import App

class CustomApp:
    def __init__(self):
        self.root_dir = "default"
        
app = CustomApp()
""")

    with patch.object(sys, "path", [*sys.path, str(tmp_path)]):
        with patch("yaaf.cli.uvicorn.run") as mock_run:
            with patch.object(sys, "argv", ["yaaf", "--app", "custom_app.app:app"]):
                try:
                    main()
                except SystemExit:
                    pass

    assert mock_run.called
    app_instance = mock_run.call_args[0][0]
    assert hasattr(app_instance, "root_dir")


def test_app_uses_custom_root_for_route_discovery(tmp_path: Path) -> None:
    """Test that App instance uses custom root directory for route discovery."""
    from yaaf.app import App

    custom_root = tmp_path / "my_root"
    route_dir = custom_root / "test"
    route_dir.mkdir(parents=True)

    (route_dir / "_service.py").write_text("class Service: pass\nservice = Service()")
    (route_dir / "_server.py").write_text("async def get(): return 'test'")

    app = App(root_dir=str(custom_root))
    assert app._root_dir == str(custom_root)

    app._ensure_routes()
    assert app._routes is not None
    assert len(app._routes) > 0
    assert any("test" in route.route_parts for route in app._routes)


def test_loader_module_loading_with_custom_root(tmp_path: Path) -> None:
    """Test that _load_module works correctly with custom root directory names."""
    from yaaf.loader import _load_module, discover_routes

    custom_root = tmp_path / "my_custom_api"
    route_dir = custom_root / "test"
    route_dir.mkdir(parents=True)

    (route_dir / "_service.py").write_text(
        "class CustomService: pass\nservice = CustomService()"
    )
    (route_dir / "_server.py").write_text("async def get(): return 'test'")

    routes, registry = discover_routes(str(custom_root))

    assert len(routes) == 1
    assert routes[0].route_parts == ["test"]
    assert "GET" in routes[0].handlers

    assert "CustomService" in registry.by_alias or "test" in registry.by_alias

    service_module = _load_module(
        route_dir / "_service.py", "service", str(custom_root)
    )
    assert hasattr(service_module, "service")
    assert hasattr(service_module, "CustomService")

    server_module = _load_module(route_dir / "_server.py", "server", str(custom_root))
    assert hasattr(server_module, "get")
