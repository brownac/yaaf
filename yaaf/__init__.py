"""yaaf package exports with lazy loading to avoid circular imports."""

from __future__ import annotations

import importlib
from typing import Any

__all__ = ["App", "Request", "Response", "app"]


def __getattr__(name: str) -> Any:
    if name in {"App", "Request", "app"}:
        app_module = importlib.import_module(f"{__name__}.app")
        return getattr(app_module, name)
    if name == "Response":
        from .responses import Response

        return Response
    raise AttributeError(f"module {__name__} has no attribute {name}")


def __dir__() -> list[str]:
    return sorted(__all__)
