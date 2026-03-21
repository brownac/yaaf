from __future__ import annotations

from typing import Protocol

from yaaf.types import Params


class NameService(Protocol):
    def greet(self, name: str) -> str: ...


async def get(params: Params, service: NameService) -> dict[str, str]:
    return {"message": service.greet(params["name"])}
