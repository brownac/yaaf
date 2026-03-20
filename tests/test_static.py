from __future__ import annotations

from pathlib import Path

import pytest

from yaaf.app import App


class DummySend:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def __call__(self, message: dict) -> None:
        self.messages.append(message)


class DummyReceive:
    def __init__(self, body: bytes = b"") -> None:
        self.body = body
        self.sent = False

    async def __call__(self) -> dict:
        if self.sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        self.sent = True
        return {"type": "http.request", "body": self.body, "more_body": False}


@pytest.mark.asyncio
async def test_static_file_serving(tmp_path: Path) -> None:
    static_dir = tmp_path / "public"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<h1>Hello</h1>")

    route_dir = tmp_path / "api" / "static" / "[...filepath]"
    route_dir.mkdir(parents=True)
    (tmp_path / "api" / "__init__.py").write_text("# package\n")

    # Use path_params for the actual params, static for the handler
    # Use absolute path to static directory
    (route_dir / "_server.py").write_text(
        "from yaaf_static import static_files\n\n"
        "async def get(path_params, static=static_files('"
        + str(static_dir).replace("\\", "\\\\")
        + "')):\n"
        "    return static(path_params)\n"
    )

    app = App(root_dir=str(tmp_path / "api"))

    send = DummySend()
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/static/index.html",
        "headers": [],
    }
    await app(scope, DummyReceive(), send)

    assert send.messages[0]["status"] == 200
    assert b"<h1>Hello</h1>" in send.messages[1]["body"]
    assert send.messages[0]["headers"][0][1] == "text/html"


@pytest.mark.asyncio
async def test_static_file_not_found(tmp_path: Path) -> None:
    static_dir = tmp_path / "public"
    static_dir.mkdir()

    route_dir = tmp_path / "api" / "static" / "[...filepath]"
    route_dir.mkdir(parents=True)
    (tmp_path / "api" / "__init__.py").write_text("# package\n")

    (route_dir / "_server.py").write_text(
        "from yaaf_static import static_files\n\n"
        "async def get(path_params, static=static_files('public')):\n"
        "    return static(path_params)\n"
    )

    app = App(root_dir=str(tmp_path / "api"))

    send = DummySend()
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/static/missing.html",
        "headers": [],
    }
    await app(scope, DummyReceive(), send)

    assert send.messages[0]["status"] == 404


@pytest.mark.asyncio
async def test_static_file_path_traversal_blocked(tmp_path: Path) -> None:
    static_dir = tmp_path / "public"
    static_dir.mkdir()

    route_dir = tmp_path / "api" / "static" / "[...filepath]"
    route_dir.mkdir(parents=True)
    (tmp_path / "api" / "__init__.py").write_text("# package\n")

    (route_dir / "_server.py").write_text(
        "from yaaf_static import static_files\n\n"
        "async def get(path_params, static=static_files('public')):\n"
        "    return static(path_params)\n"
    )

    app = App(root_dir=str(tmp_path / "api"))

    send = DummySend()
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/static/../../etc/passwd",
        "headers": [],
    }
    await app(scope, DummyReceive(), send)

    assert send.messages[0]["status"] == 403


@pytest.mark.asyncio
async def test_catch_all_route_pattern(tmp_path: Path) -> None:
    from yaaf.loader import build_pattern

    pattern, params, static_count, segment_count = build_pattern(
        ["static", "[...filepath]"], prefix=""
    )

    assert params == ["filepath"]
    assert static_count == 1
    assert segment_count == 2

    import re

    compiled = re.compile(pattern)
    match = compiled.match("/static/css/style.css")
    assert match is not None
    assert match.group("filepath") == "css/style.css"


# Unit tests for StaticHandler class

from yaaf_static import StaticHandler, static_files


def test_static_handler_subdirectory_file(tmp_path: Path) -> None:
    """Test serving files from subdirectories."""
    static_dir = tmp_path / "public"
    static_dir.mkdir()
    css_dir = static_dir / "css"
    css_dir.mkdir()
    (css_dir / "style.css").write_text("body { color: red; }")

    handler = StaticHandler(str(static_dir))
    response = handler({"filepath": "css/style.css"})

    assert response.status == 200
    assert b"body { color: red; }" in response.body
    # Headers are str tuples in yaaf_static
    headers = dict(response.headers or [])
    assert headers.get("Content-Type") == "text/css"


def test_static_handler_json_mime_type(tmp_path: Path) -> None:
    """Test that JSON files get correct MIME type."""
    static_dir = tmp_path / "public"
    static_dir.mkdir()
    (static_dir / "data.json").write_text('{"key": "value"}')

    handler = StaticHandler(str(static_dir))
    response = handler({"filepath": "data.json"})

    headers = dict(response.headers or [])
    assert headers.get("Content-Type") == "application/json"


def test_static_handler_binary_file(tmp_path: Path) -> None:
    """Test that binary files get application/octet-stream."""
    static_dir = tmp_path / "public"
    static_dir.mkdir()
    (static_dir / "binary.bin").write_bytes(b"\x00\x01\x02\x03")

    handler = StaticHandler(str(static_dir))
    response = handler({"filepath": "binary.bin"})

    headers = dict(response.headers or [])
    assert headers.get("Content-Type") == "application/octet-stream"


def test_static_handler_directory_index(tmp_path: Path) -> None:
    """Test directory index fallback."""
    static_dir = tmp_path / "public"
    static_dir.mkdir()
    subdir = static_dir / "subdir"
    subdir.mkdir()
    (subdir / "index.html").write_text("<h1>Subdir Index</h1>")

    handler = StaticHandler(str(static_dir))
    # When path is a directory, should serve index.html from that directory
    response = handler({"filepath": "subdir"})

    assert response.status == 200
    assert b"<h1>Subdir Index</h1>" in response.body


def test_static_handler_root_index(tmp_path: Path) -> None:
    """Test serving index.html at root."""
    static_dir = tmp_path / "public"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<h1>Root Index</h1>")

    handler = StaticHandler(str(static_dir))
    # Empty/null filepath should serve index
    response = handler({})

    assert response.status == 200
    assert b"<h1>Root Index</h1>" in response.body


def test_static_handler_none_path_params(tmp_path: Path) -> None:
    """Test handler with None path_params."""
    static_dir = tmp_path / "public"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<h1>Index</h1>")

    handler = StaticHandler(str(static_dir))
    response = handler(None)

    assert response.status == 200


def test_static_handler_absolute_path_blocked(tmp_path: Path) -> None:
    """Test that absolute paths are blocked."""
    static_dir = tmp_path / "public"
    static_dir.mkdir()

    handler = StaticHandler(str(static_dir))
    response = handler({"filepath": "/etc/passwd"})

    assert response.status == 403


def test_static_handler_dotdot_blocked(tmp_path: Path) -> None:
    """Test that .. in path is blocked."""
    static_dir = tmp_path / "public"
    static_dir.mkdir()

    handler = StaticHandler(str(static_dir))
    response = handler({"filepath": "subdir/../../../etc/passwd"})

    assert response.status == 403


def test_static_handler_symlink_outside_blocked(tmp_path: Path) -> None:
    """Test that symlinks pointing outside are blocked."""
    static_dir = tmp_path / "public"
    static_dir.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("secret data")
    # Create symlink inside public to outside
    symlink = static_dir / "link_to_secret"
    try:
        symlink.symlink_to(secret)

        handler = StaticHandler(str(static_dir))
        response = handler({"filepath": "link_to_secret"})

        assert response.status == 403
    except (OSError, NotImplementedError):
        # Symlinks may not be supported on Windows in some contexts
        pytest.skip("Symlinks not supported")


def test_static_files_factory_function(tmp_path: Path) -> None:
    """Test the static_files() factory function."""
    static_dir = tmp_path / "public"
    static_dir.mkdir()
    (static_dir / "test.txt").write_text("hello")

    handler = static_files(str(static_dir), index="index.html")

    assert isinstance(handler, StaticHandler)
    assert handler.directory == static_dir.resolve()
    assert handler.index == "index.html"

    response = handler({"filepath": "test.txt"})
    assert response.status == 200
    assert response.body == b"hello"


def test_static_handler_custom_index(tmp_path: Path) -> None:
    """Test custom index file name."""
    static_dir = tmp_path / "public"
    static_dir.mkdir()
    (static_dir / "welcome.htm").write_text("<h1>Welcome</h1>")

    handler = StaticHandler(str(static_dir), index="welcome.htm")
    response = handler({"filepath": "subdir"})

    # Non-existent subdir should try to look for welcome.htm, not index.html
    assert response.status == 404  # subdir doesn't exist
