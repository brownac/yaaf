from __future__ import annotations

from typing import Protocol

from yaaf import Request


class HelloService(Protocol):
    def message(self) -> str: ...


async def get(request: Request, service: HelloService) -> dict[str, str]:
    return {"message": service.message(), "path": request.path}
