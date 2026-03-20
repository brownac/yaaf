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


def _write_service(path: Path, code: str) -> None:
    (path / "_service.py").write_text(code)


def _write_server(path: Path, code: str) -> None:
    (path / "_server.py").write_text(code)


@pytest.mark.asyncio
async def test_app_routes_and_params(tmp_path: Path) -> None:
    base = tmp_path / "api"
    hello = base / "hello"
    hello.mkdir(parents=True)
    (tmp_path / "api" / "__init__.py").write_text("# package\n")

    _write_service(
        hello,
        "from yaaf import service\n\n"
        "@service('HelloService')\n"
        "class HelloService:\n"
        "    def message(self) -> str:\n"
        "        return 'hi'\n\n"
        "service = HelloService\n",
    )
    _write_server(
        hello,
        "from api.hello._service import HelloService\n"
        "from yaaf import Request\n\n"
        "async def get(request: Request, service: HelloService):\n"
        "    return {'message': service.message(), 'path': request.path}\n",
    )

    app = App(root_dir=str(tmp_path / "api"))

    send = DummySend()
    scope = {"type": "http", "method": "GET", "path": "/hello", "headers": []}
    await app(scope, DummyReceive(), send)
    assert send.messages[0]["status"] == 200
    assert b"hi" in send.messages[1]["body"]


@pytest.mark.asyncio
async def test_app_not_found(tmp_path: Path) -> None:
    base = tmp_path / "api" / "hello"
    base.mkdir(parents=True)
    (tmp_path / "api" / "__init__.py").write_text("# package\n")
    _write_service(base, "class Service:...\nservice = Service()\n")
    _write_server(base, "async def get():...\n")

    app = App(root_dir=str(tmp_path / "api"))

    send = DummySend()
    scope = {"type": "http", "method": "GET", "path": "/missing", "headers": []}
    await app(scope, DummyReceive(), send)
    assert send.messages[0]["status"] == 404
