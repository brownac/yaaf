from __future__ import annotations

from typing import TYPE_CHECKING

from yaaf.types import Params
from yaaf_static import static_files

if TYPE_CHECKING:
    from yaaf_static import StaticHandler


async def get(
    path_params: Params, static: StaticHandler = static_files("public")
) -> dict:
    return static(path_params)
