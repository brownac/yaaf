"""Tests for all supported HTTP verbs."""

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


def _setup_echo_route(base: Path) -> None:
    route = base / "echo"
    route.mkdir(parents=True)
    (base / "__init__.py").write_text("# package\n")
    (route / "_service.py").write_text(
        "from yaaf import service\n\n"
        "@service('EchoService')\n"
        "class EchoService:\n"
        "    def echo(self, data: str) -> str:\n"
        "        return f'echo: {data}'\n\n"
        "service = EchoService\n"
    )
    (route / "_server.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "from typing import Protocol\n"
        "\n"
        "from yaaf import Request\n"
        "\n"
        "\n"
        "class EchoService(Protocol):\n"
        "    def echo(self, data: str) -> str: ...\n"
        "\n"
        "\n"
        "async def get(request: Request, service: EchoService) -> dict:\n"
        "    return {'method': 'GET', 'data': service.echo('get')}\n"
        "\n"
        "\n"
        "async def post(request: Request, service: EchoService) -> dict:\n"
        "    body = request.text()\n"
        "    return {'method': 'POST', 'data': service.echo(body)}\n"
        "\n"
        "\n"
        "async def put(request: Request, service: EchoService) -> dict:\n"
        "    body = request.text()\n"
        "    return {'method': 'PUT', 'data': service.echo(body)}\n"
        "\n"
        "\n"
        "async def delete(request: Request, service: EchoService) -> dict:\n"
        "    return {'method': 'DELETE', 'data': service.echo('delete')}\n"
        "\n"
        "\n"
        "async def patch(request: Request, service: EchoService) -> dict:\n"
        "    body = request.text()\n"
        "    return {'method': 'PATCH', 'data': service.echo(body)}\n"
        "\n"
        "\n"
        "async def options(request: Request, service: EchoService) -> dict:\n"
        "    return {'method': 'OPTIONS', 'data': service.echo('options')}\n"
        "\n"
        "\n"
        "async def head(request: Request, service: EchoService) -> dict:\n"
        "    return {'method': 'HEAD', 'data': service.echo('head')}\n"
    )


@pytest.mark.asyncio
async def test_get(tmp_path: Path) -> None:
    _setup_echo_route(tmp_path / "api")
    app = App(root_dir=str(tmp_path / "api"))

    send = DummySend()
    await app(
        {"type": "http", "method": "GET", "path": "/echo", "headers": []},
        DummyReceive(),
        send,
    )

    assert send.messages[0]["status"] == 200
    assert b"GET" in send.messages[1]["body"]
    assert b'"method": "GET"' in send.messages[1]["body"]


@pytest.mark.asyncio
async def test_post(tmp_path: Path) -> None:
    _setup_echo_route(tmp_path / "api")
    app = App(root_dir=str(tmp_path / "api"))

    send = DummySend()
    body = b"hello world"
    await app(
        {"type": "http", "method": "POST", "path": "/echo", "headers": []},
        DummyReceive(body),
        send,
    )

    assert send.messages[0]["status"] == 200
    assert b"POST" in send.messages[1]["body"]
    assert b"hello world" in send.messages[1]["body"]


@pytest.mark.asyncio
async def test_put(tmp_path: Path) -> None:
    _setup_echo_route(tmp_path / "api")
    app = App(root_dir=str(tmp_path / "api"))

    send = DummySend()
    body = b"update data"
    await app(
        {"type": "http", "method": "PUT", "path": "/echo", "headers": []},
        DummyReceive(body),
        send,
    )

    assert send.messages[0]["status"] == 200
    assert b"PUT" in send.messages[1]["body"]
    assert b"update data" in send.messages[1]["body"]


@pytest.mark.asyncio
async def test_delete(tmp_path: Path) -> None:
    _setup_echo_route(tmp_path / "api")
    app = App(root_dir=str(tmp_path / "api"))

    send = DummySend()
    await app(
        {"type": "http", "method": "DELETE", "path": "/echo", "headers": []},
        DummyReceive(),
        send,
    )

    assert send.messages[0]["status"] == 200
    assert b"DELETE" in send.messages[1]["body"]


@pytest.mark.asyncio
async def test_patch(tmp_path: Path) -> None:
    _setup_echo_route(tmp_path / "api")
    app = App(root_dir=str(tmp_path / "api"))

    send = DummySend()
    body = b"patch data"
    await app(
        {"type": "http", "method": "PATCH", "path": "/echo", "headers": []},
        DummyReceive(body),
        send,
    )

    assert send.messages[0]["status"] == 200
    assert b"PATCH" in send.messages[1]["body"]
    assert b"patch data" in send.messages[1]["body"]


@pytest.mark.asyncio
async def test_options(tmp_path: Path) -> None:
    _setup_echo_route(tmp_path / "api")
    app = App(root_dir=str(tmp_path / "api"))

    send = DummySend()
    await app(
        {"type": "http", "method": "OPTIONS", "path": "/echo", "headers": []},
        DummyReceive(),
        send,
    )

    assert send.messages[0]["status"] == 200
    assert b"OPTIONS" in send.messages[1]["body"]


@pytest.mark.asyncio
async def test_head(tmp_path: Path) -> None:
    _setup_echo_route(tmp_path / "api")
    app = App(root_dir=str(tmp_path / "api"))

    send = DummySend()
    await app(
        {"type": "http", "method": "HEAD", "path": "/echo", "headers": []},
        DummyReceive(),
        send,
    )

    assert send.messages[0]["status"] == 200


@pytest.mark.asyncio
async def test_unsupported_method(tmp_path: Path) -> None:
    _setup_echo_route(tmp_path / "api")
    app = App(root_dir=str(tmp_path / "api"))

    send = DummySend()
    await app(
        {"type": "http", "method": "TRACE", "path": "/echo", "headers": []},
        DummyReceive(),
        send,
    )

    assert send.messages[0]["status"] == 404
