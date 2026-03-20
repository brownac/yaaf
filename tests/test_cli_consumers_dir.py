"""Test CLI functionality with custom consumers directory."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from yaaf.cli import main


def test_cli_serve_with_default_app_uses_custom_consumers_dir(tmp_path: Path) -> None:
    """Test that serve command with default app uses custom consumers directory."""
    custom_consumers = tmp_path / "my_consumers"
    api_dir = custom_consumers / "api" / "hello"
    api_dir.mkdir(parents=True)

    (api_dir / "_service.py").write_text("class Service: pass\nservice = Service()")
    (api_dir / "_server.py").write_text("async def get(): return 'Hello'")

    with patch("yaaf.cli.uvicorn.run") as mock_run:
        with patch.object(
            sys,
            "argv",
            ["yaaf", "--consumers-dir", str(custom_consumers), "--port", "8001"],
        ):
            try:
                main()
            except SystemExit:
                pass

    assert mock_run.called
    app_instance = mock_run.call_args[0][0]
    assert app_instance._consumers_dir == str(custom_consumers)


def test_cli_serve_with_custom_app_path(tmp_path: Path) -> None:
    """Test that serve command with custom app path works correctly."""
    custom_app_dir = tmp_path / "custom_app"
    custom_app_dir.mkdir()

    (custom_app_dir / "__init__.py").write_text("")
    (custom_app_dir / "app.py").write_text("""
from yaaf.app import App

class CustomApp:
    def __init__(self):
        self.consumers_dir = "default"
        
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
    assert hasattr(app_instance, "consumers_dir")


def test_app_uses_custom_consumers_dir_for_route_discovery(tmp_path: Path) -> None:
    """Test that App instance uses custom consumers directory for route discovery."""
    from yaaf.app import App

    custom_consumers = tmp_path / "my_consumers"
    api_dir = custom_consumers / "api" / "test"
    api_dir.mkdir(parents=True)

    (api_dir / "_service.py").write_text("class Service: pass\nservice = Service()")
    (api_dir / "_server.py").write_text("async def get(): return 'test'")

    app = App(consumers_dir=str(custom_consumers))
    assert app._consumers_dir == str(custom_consumers)

    app._ensure_routes()
    assert app._routes is not None
    assert len(app._routes) > 0
    assert any("test" in route.route_parts for route in app._routes)


def test_loader_module_loading_with_custom_consumers_dir(tmp_path: Path) -> None:
    """Test that _load_module works correctly with custom consumers directory names."""
    from yaaf.loader import _load_module, discover_routes

    custom_consumers = tmp_path / "my_custom_api"
    api_dir = custom_consumers / "api" / "test"
    api_dir.mkdir(parents=True)

    (api_dir / "_service.py").write_text(
        "class CustomService: pass\nservice = CustomService()"
    )
    (api_dir / "_server.py").write_text("async def get(): return 'test'")

    routes, registry = discover_routes(str(custom_consumers))

    assert len(routes) == 1
    assert routes[0].route_parts == ["test"]
    assert "GET" in routes[0].handlers

    assert "CustomService" in registry.by_alias or "test" in registry.by_alias

    service_module = _load_module(
        api_dir / "_service.py", "service", str(custom_consumers)
    )
    assert hasattr(service_module, "service")
    assert hasattr(service_module, "CustomService")

    server_module = _load_module(
        api_dir / "_server.py", "server", str(custom_consumers)
    )
    assert hasattr(server_module, "get")
