"""Filesystem-routed ASGI app for yaaf."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any

from .di import DependencyResolver
from .loader import discover_routes
from .responses import Response, as_response
from .types import ASGIScope, ASGIReceive, ASGISend, Params


@dataclass
class Request:
    """Represents an HTTP request within the ASGI app."""
    scope: ASGIScope
    body: bytes
    path_params: Params

    @property
    def method(self) -> str:
        """Return the HTTP method."""
        return self.scope.get("method", "").upper()

    @property
    def path(self) -> str:
        """Return the request path."""
        return self.scope.get("path", "")

    @property
    def headers(self) -> dict[str, str]:
        """Return decoded request headers."""
        raw = self.scope.get("headers", [])
        return {k.decode(): v.decode() for k, v in raw}

    def text(self) -> str:
        """Return the request body as text."""
        return self.body.decode()


class App:
    """Filesystem-routed ASGI interface."""

    def __init__(self, consumers_dir: str = "consumers") -> None:
        """Initialize the app by discovering filesystem routes."""
        self._consumers_dir = consumers_dir
        self._routes = None
        self._registry = None
        self._resolver = None

    def _ensure_routes(self) -> None:
        if self._routes is None or self._registry is None or self._resolver is None:
            self._routes, self._registry = discover_routes(self._consumers_dir)
            self._resolver = DependencyResolver(self._registry)

    async def __call__(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        """ASGI entrypoint."""
        self._ensure_routes()
        if scope.get("type") != "http":
            response = Response.text("Unsupported scope type", status=500)
            await response.send(send)
            return

        method = scope.get("method", "").upper()
        path = scope.get("path", "")
        match = None
        for route in self._routes or []:
            if method not in route.handlers:
                continue
            result = route.pattern.match(path)
            if result is None:
                continue
            match = (route, result.groups())
            break

        if match is None:
            response = Response.text("Not Found", status=404)
            await response.send(send)
            return
        route, groups = match

        body = b""
        more_body = True
        while more_body:
            message = await receive()
            if message.get("type") != "http.request":
                break
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        path_params = dict(zip(route.param_names, groups))
        request = Request(scope=scope, body=body, path_params=path_params)
        handler = route.handlers[method]
        context = {
            "request": request,
            "params": path_params,
            "path_params": path_params,
        }
        result = self._resolver.call(handler, context)
        if inspect.isawaitable(result):
            result = await result

        response = as_response(result)
        await response.send(send)


app = App()
