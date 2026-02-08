"""Test CLI functionality with custom consumers directory."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from yaaf.cli import main
from yaaf.gen_services import generate_services


def test_cli_gen_services_with_custom_consumers_dir(tmp_path: Path) -> None:
    """Test that gen-services command uses custom consumers directory."""
    # Create a custom consumers directory structure
    custom_consumers = tmp_path / "my_consumers"
    api_dir = custom_consumers / "api" / "test"
    api_dir.mkdir(parents=True)
    
    (api_dir / "_service.py").write_text("class Service: pass\nservice = Service()")
    
    output_file = tmp_path / "output.py"
    
    # Test the generate_services function directly
    result_path = generate_services(
        consumers_dir=str(custom_consumers),
        output_path=str(output_file)
    )
    
    assert result_path == output_file
    assert output_file.exists()
    content = output_file.read_text()
    assert "TestService" in content


def test_cli_serve_with_default_app_uses_custom_consumers_dir(tmp_path: Path) -> None:
    """Test that serve command with default app uses custom consumers directory."""
    # Create a custom consumers directory structure
    custom_consumers = tmp_path / "my_consumers"
    api_dir = custom_consumers / "api" / "hello"
    api_dir.mkdir(parents=True)
    
    (api_dir / "_service.py").write_text("class Service: pass\nservice = Service()")
    (api_dir / "_server.py").write_text("async def get(): return 'Hello'")
    
    # Mock uvicorn.run to capture the app instance
    with patch('yaaf.cli.uvicorn.run') as mock_run:
        # Mock sys.argv to simulate CLI call
        with patch.object(sys, 'argv', ['yaaf', '--consumers-dir', str(custom_consumers), '--port', '8001']):
            try:
                main()
            except SystemExit:
                pass  # Expected when uvicorn.run is mocked
    
    # Verify uvicorn.run was called
    assert mock_run.called
    
    # Get the app instance that was passed to uvicorn.run
    app_instance = mock_run.call_args[0][0]
    
    # Verify the app has the correct consumers_dir
    assert app_instance._consumers_dir == str(custom_consumers)


def test_cli_serve_with_custom_app_path(tmp_path: Path) -> None:
    """Test that serve command with custom app path works correctly."""
    # Create a custom app module
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
    
    # Add the temp directory to sys.path so the custom app can be imported
    with patch.object(sys, 'path', [*sys.path, str(tmp_path)]):
        with patch('yaaf.cli.uvicorn.run') as mock_run:
            with patch.object(sys, 'argv', ['yaaf', '--app', 'custom_app.app:app']):
                try:
                    main()
                except SystemExit:
                    pass  # Expected when uvicorn.run is mocked
    
    # Verify uvicorn.run was called with the custom app
    assert mock_run.called
    app_instance = mock_run.call_args[0][0]
    assert hasattr(app_instance, 'consumers_dir')


def test_cli_gen_services_command_parsing(tmp_path: Path) -> None:
    """Test that gen-services command correctly parses arguments."""
    custom_consumers = tmp_path / "custom_consumers"
    custom_consumers.mkdir()
    
    output_file = tmp_path / "custom_output.py"
    
    with patch('yaaf.cli.generate_services') as mock_generate:
        with patch.object(sys, 'argv', ['yaaf', 'gen-services', '--consumers-dir', str(custom_consumers), '--output', str(output_file)]):
            try:
                main()
            except SystemExit:
                pass  # Expected when function returns early
    
    # Verify generate_services was called with correct arguments
    assert mock_generate.called
    call_args = mock_generate.call_args[1]
    assert call_args['consumers_dir'] == str(custom_consumers)
    assert call_args['output_path'] == str(output_file)


def test_cli_serve_command_generates_services_with_custom_dir(tmp_path: Path) -> None:
    """Test that serve command generates services using custom consumers directory."""
    custom_consumers = tmp_path / "my_consumers"
    custom_consumers.mkdir()
    
    with patch('yaaf.cli.uvicorn.run') as mock_run:
        with patch('yaaf.cli.generate_services') as mock_generate:
            with patch.object(sys, 'argv', ['yaaf', '--consumers-dir', str(custom_consumers)]):
                try:
                    main()
                except SystemExit:
                    pass  # Expected when uvicorn.run is mocked
    
    # Verify generate_services was called with the custom consumers directory
    assert mock_generate.called
    call_args = mock_generate.call_args[1]
    assert call_args['consumers_dir'] == str(custom_consumers)


def test_app_uses_custom_consumers_dir_for_route_discovery(tmp_path: Path) -> None:
    """Test that App instance uses custom consumers directory for route discovery."""
    from yaaf.app import App
    
    # Create a custom consumers directory structure
    custom_consumers = tmp_path / "my_consumers"
    api_dir = custom_consumers / "api" / "test"
    api_dir.mkdir(parents=True)
    
    (api_dir / "_service.py").write_text("class Service: pass\nservice = Service()")
    (api_dir / "_server.py").write_text("async def get(): return 'test'")
    
    # Create app with custom consumers directory
    app = App(consumers_dir=str(custom_consumers))
    
    # Verify the consumers directory is set
    assert app._consumers_dir == str(custom_consumers)
    
    # Trigger route discovery
    app._ensure_routes()
    
    # Verify routes were discovered from the custom directory
    assert len(app._routes) > 0
    assert any("test" in route.route_parts for route in app._routes)
