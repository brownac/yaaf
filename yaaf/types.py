"""Shared type aliases for yaaf."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from .responses import Response

ASGIScope: TypeAlias = dict[str, Any]
ASGIReceive: TypeAlias = Callable[[], Awaitable[dict[str, Any]]]
ASGISend: TypeAlias = Callable[[dict[str, Any]], Awaitable[None]]

Params: TypeAlias = dict[str, str]
ResponseLike: TypeAlias = (
    "Response | str | bytes | dict[str, Any] | list[Any] | tuple[Any, int]"
)
Handler: TypeAlias = Callable[..., ResponseLike | Awaitable[ResponseLike]]
