"""Simple dependency injection for yaaf services and handlers."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any, Callable, TypeVar

T = TypeVar("T")

@dataclass
class ServiceRegistry:
    """Global registry for services, keyed by type and name variants."""
    by_type: dict[type[Any], Any]
    by_alias: dict[str, Any]

    def register(self, instance: T, aliases: list[str]) -> T:
        """Register a service instance by type and alias names."""
        self.by_type[type(instance)] = instance
        type_name = type(instance).__name__
        if type_name:
            self.by_alias[type_name] = instance
        for alias in aliases:
            self.by_alias[alias] = instance
        return instance

    def resolve(self, annotation: type | None) -> Any | None:
        """Resolve a service by type annotation."""
        if isinstance(annotation, str):
            return self.by_alias.get(annotation)
        if annotation is not None:
            # Direct type match
            if annotation in self.by_type:
                return self.by_type[annotation]
            
            # Check for protocol/base class relationships
            for registered_type, instance in self.by_type.items():
                try:
                    # Check if registered type is a subclass of the annotation
                    if issubclass(registered_type, annotation):
                        return instance
                except (TypeError, AttributeError):
                    # Handle cases where issubclass fails (e.g., for Protocol types)
                    pass
            
            # Try to resolve by name as fallback
            alias = getattr(annotation, "__name__", "")
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
