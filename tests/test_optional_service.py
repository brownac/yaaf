
import pytest
from pathlib import Path
from yaaf.app import App

class DummySend:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def __call__(self, message: dict) -> None:
        self.messages.append(message)

class DummyReceive:
    def __init__(self) -> None:
        self.sent = False

    async def __call__(self) -> dict:
        if self.sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        self.sent = True
        return {"type": "http.request", "body": b"", "more_body": False}

@pytest.mark.asyncio
async def test_route_without_service_file(tmp_path: Path) -> None:
    # Setup a fresh consumer structure
    base = tmp_path / "consumers" / "api" / "noservice"
    base.mkdir(parents=True)
    
    # Only write _server.py, NO _service.py
    (base / "_server.py").write_text(
        "from yaaf import Request\n"
        "async def get(request: Request):\n"
        "    return {'message': 'ok without service'}\n"
    )
    (tmp_path / "consumers" / "api" / "__init__.py").write_text("# package\n")

    app = App(consumers_dir=str(tmp_path / "consumers"))

    send = DummySend()
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/noservice",
        "headers": [],
    }
    
    await app(scope, DummyReceive(), send)
    
    # Expectation: Should fail (404) currently, but we want 200
    assert send.messages[0]["status"] == 200
    assert b"ok without service" in send.messages[1]["body"]
