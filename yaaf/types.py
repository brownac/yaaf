"""Shared type aliases and protocols for yaaf."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Protocol, TYPE_CHECKING, TypeAlias, TypeVar

if TYPE_CHECKING:
    from .responses import Response
    from .app import Request

ASGIScope: TypeAlias = dict[str, Any]
ASGIReceive: TypeAlias = Callable[[], Awaitable[dict[str, Any]]]
ASGISend: TypeAlias = Callable[[dict[str, Any]], Awaitable[None]]

Params: TypeAlias = dict[str, str]
ResponseLike: TypeAlias = "Response | str | bytes | dict[str, Any] | list[Any] | tuple[Any, int]"
Handler: TypeAlias = Callable[..., ResponseLike | Awaitable[ResponseLike]]


class ServiceProtocol(Protocol):
    """Marker protocol for services registered with yaaf."""


ServiceT = TypeVar("ServiceT", bound=ServiceProtocol)


class ServerHandler(Protocol):
    """Preferred handler signature for type checking."""

    def __call__(
        self,
        request: "Request",
        params: Params,
        path_params: Params,
        service: Any | None,
    ) -> ResponseLike | Awaitable[ResponseLike]:
        ...


class ServiceFactory(Protocol):
    """Callable factory that builds a service with DI-injected args."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        ...
