from __future__ import annotations

from typing import Protocol


class FooBarBazService(Protocol):
    def get_name(self) -> str: ...


async def get(service: FooBarBazService) -> dict[str, str]:
    return {"message": f"Hello from {service.get_name()}"}
