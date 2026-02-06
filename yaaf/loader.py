"""Filesystem route discovery and module loading."""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from .di import DependencyResolver, ServiceRegistry
from .types import Handler


@dataclass
class RouteTarget:
    """A discovered filesystem route and its handlers/services."""
    pattern: re.Pattern[str]
    route_parts: list[str]
    param_names: list[str]
    handlers: dict[str, Handler]
    services: ServiceRegistry
    service: Any | None
    static_count: int
    segment_count: int


def _load_module(path: Path, name_prefix: str) -> ModuleType:
    """Load a Python module from an explicit file path."""
    module_name = f"yaaf_{name_prefix}_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _collect_services(module: ModuleType, resolver: DependencyResolver) -> Any | None:
    """Create a service from a module, if it exposes one."""
    if hasattr(module, "service"):
        instance = getattr(module, "service")
        if instance is not None:
            if callable(instance):
                return resolver.call(instance, {})
            return instance
    if hasattr(module, "get_service") and callable(module.get_service):
        return resolver.call(module.get_service, {})
    if hasattr(module, "Service"):
        service_cls = module.Service
        if callable(service_cls):
            return resolver.call(service_cls, {})
    return None


def discover_routes(consumers_dir: str) -> tuple[list[RouteTarget], ServiceRegistry]:
    """Discover route handlers and services rooted under a consumers directory."""
    base = Path(consumers_dir)
    if not base.exists():
        return [], ServiceRegistry(by_type={}, by_alias={})

    base_parent = str(base.parent)
    if base_parent not in sys.path:
        sys.path.insert(0, base_parent)

    targets: list[tuple[Path, list[str], list[str], str, int, int]] = []
    service_modules: dict[Path, ModuleType] = {}
    server_modules: dict[Path, ModuleType] = {}
    service_aliases: dict[Path, list[str]] = {}

    for root, _dirs, files in os.walk(base):
        if "_server.py" not in files:
            continue

        root_path = Path(root)
        parts = root_path.parts
        if "api" not in parts:
            continue
        api_index = parts.index("api")
        route_parts = list(parts[api_index + 1 :])
        pattern, param_names, static_count, segment_count = build_pattern(route_parts, prefix="api")
        targets.append((root_path, route_parts, param_names, pattern, static_count, segment_count))

        route_key = "_".join(route_parts)
        aliases = [route_key, _service_alias(route_parts)]
        if route_parts:
            aliases.append(route_parts[-1])
        service_aliases[root_path] = [alias for alias in aliases if alias]

        if "_service.py" in files:
            service_modules[root_path] = _load_module(root_path / "_service.py", "service")
        server_modules[root_path] = _load_module(root_path / "_server.py", "server")

    registry = ServiceRegistry(by_type={}, by_alias={})
    resolver = DependencyResolver(registry)

    service_instances: dict[Path, Any] = {}
    unresolved = list(service_modules.items())
    while unresolved:
        progress = False
        remaining: list[tuple[Path, ModuleType]] = []
        for path, module in unresolved:
            try:
                instance = _collect_services(module, resolver)
            except TypeError:
                instance = None
            if instance is None:
                remaining.append((path, module))
                continue
            service_instances[path] = instance
            registry.register(instance, aliases=service_aliases.get(path, []))
            progress = True
        if not progress:
            missing = [str(path) for path, _ in remaining]
            raise RuntimeError(f"Unresolved service dependencies in: {', '.join(missing)}")
        unresolved = remaining

    routes: list[RouteTarget] = []
    for root_path, route_parts, param_names, pattern, static_count, segment_count in targets:
        server_module = server_modules[root_path]
        handlers: dict[str, Handler] = {}
        for method in ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"):
            func = getattr(server_module, method.lower(), None)
            if callable(func):
                handlers[method] = func
        compiled = re.compile(pattern)
        service_instance = service_instances.get(root_path)
        routes.append(
            RouteTarget(
                pattern=compiled,
                route_parts=route_parts,
                param_names=param_names,
                handlers=handlers,
        services=registry,
        service=service_instance,
        static_count=static_count,
        segment_count=segment_count,
    )
        )

    routes.sort(key=lambda route: (route.static_count, route.segment_count), reverse=True)

    static_routes = [route for route in routes if not route.param_names]
    dynamic_routes = [route for route in routes if route.param_names]
    for dyn in dynamic_routes:
        for stat in static_routes:
            if dyn.segment_count != stat.segment_count:
                continue
            candidate = "/api/" + "/".join(stat.route_parts)
            if dyn.pattern.match(candidate):
                print(
                    f"Warning: dynamic route /api/{'/'.join(dyn.route_parts)} matches "
                    f"static route /api/{'/'.join(stat.route_parts)}"
                )
                break
    return routes, registry


def build_pattern(route_parts: list[str], prefix: str) -> tuple[str, list[str], int, int]:
    """Build a regex pattern and metadata for a route path."""
    if not route_parts:
        return rf"^/{re.escape(prefix)}$", [], 0, 0

    param_names: list[str] = []
    pattern_parts: list[str] = []
    static_count = 0
    for part in route_parts:
        if part.startswith("[") and part.endswith("]"):
            name = part[1:-1]
            if not name:
                raise ValueError("Empty dynamic route segment")
            param_names.append(name)
            pattern_parts.append(r"([^/]+)")
        else:
            pattern_parts.append(re.escape(part))
            static_count += 1

    pattern = "^/" + re.escape(prefix) + "/" + "/".join(pattern_parts) + "$"
    return pattern, param_names, static_count, len(route_parts)


def _service_alias(route_parts: list[str]) -> str:
    def strip_dynamic(segment: str) -> str:
        if segment.startswith("[") and segment.endswith("]"):
            return segment[1:-1]
        return segment

    parts = [strip_dynamic(part) for part in route_parts]
    safe = [part for part in parts if part.isidentifier()]
    base = "".join(part[:1].upper() + part[1:] for part in safe) or "Route"
    return f"{base}Service"
