from __future__ import annotations

from typing import Protocol

from yaaf.types import Params


class UsersService(Protocol):
    def get_user(self, user_id: str) -> dict[str, str]: ...


async def get(params: Params, service: UsersService) -> dict[str, str]:
    user_id = params.get("id", "1")
    return service.get_user(user_id)
