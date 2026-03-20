"""Simple dependency injection for yaaf services and handlers."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def service(name: str | None = None, *, aliases: list[str] | None = None):
    """Decorator to mark a class as a yaaf service.

    Args:
        name: Custom service name for DI resolution. Defaults to class name.
        aliases: Additional names this service can be resolved by.

    Example:
        @service("CustomName", aliases=["custom", "cn"])
        class MyService:
            def do_something(self) -> str:
                return "done"

        # In a handler, inject by type or any alias:
        async def get(service: MyService) -> dict:
            # or: service: "CustomName", service: "custom", etc.
            return {"result": service.do_something()}
    """

    def decorator(cls: type[T]) -> type[T]:
        setattr(cls, "__yaaf_service__", True)
        setattr(cls, "__yaaf_service_name__", name)
        setattr(cls, "__yaaf_service_aliases__", aliases or [])
        return cls

    return decorator


def _get_service_metadata(cls: type) -> tuple[str | None, list[str]]:
    """Extract yaaf service metadata from a class."""
    name = getattr(cls, "__yaaf_service_name__", None)
    aliases: list[str] = getattr(cls, "__yaaf_service_aliases__", [])
    return name, aliases


@dataclass
class ServiceRegistry:
    """Global registry for services, keyed by type and name variants."""

    by_type: dict[type[Any], Any] = field(default_factory=dict)
    by_alias: dict[str, Any] = field(default_factory=dict)

    def register(self, instance: T, aliases: list[str] | None = None) -> T:
        """Register a service instance by type and name variants."""
        inst_type = type(instance)
        self.by_type[inst_type] = instance

        name, yaaf_aliases = _get_service_metadata(inst_type)
        resolved_name = name or inst_type.__name__
        self.by_alias[resolved_name] = instance

        for alias in yaaf_aliases or []:
            self.by_alias[alias] = instance

        for alias in aliases or []:
            self.by_alias[alias] = instance

        return instance

    def resolve(self, annotation: type | None) -> Any | None:
        """Resolve a service by type annotation."""
        if isinstance(annotation, str):
            return self.by_alias.get(annotation)
        if annotation is not None:
            if annotation in self.by_type:
                return self.by_type[annotation]

            if annotation in self.by_type.values():
                return annotation

            for registered_type, instance in self.by_type.items():
                try:
                    if issubclass(registered_type, annotation):
                        return instance
                except (TypeError, AttributeError):
                    pass

            alias = getattr(annotation, "__name__", "") or getattr(
                getattr(annotation, "__class__", None), "__name__", ""
            )
            if alias and alias in self.by_alias:
                return self.by_alias[alias]
        return None


class DependencyResolver:
    """Resolve function arguments from a registry and contextual values."""

    def __init__(self, registry: ServiceRegistry) -> None:
        """Create a resolver bound to a service registry."""
        self.registry = registry

    def call(self, func: Callable[..., Any], context: Mapping[str, Any]) -> Any:
        """Call a function, injecting dependencies from context or registry."""
        signature = inspect.signature(func)
        kwargs: dict[str, Any] = {}
        for name, param in signature.parameters.items():
            if name in context:
                kwargs[name] = context[name]
                continue
            annotation = None
            if param.annotation is not inspect._empty:
                annotation = param.annotation
            resolved = self.registry.resolve(annotation)
            if resolved is not None:
                kwargs[name] = resolved
                continue
            if param.default is not inspect._empty:
                continue
            raise TypeError(f"Cannot resolve dependency '{name}' for {func}")
        return func(**kwargs)
