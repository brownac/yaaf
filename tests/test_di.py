from __future__ import annotations

import pytest

from yaaf.di import DependencyResolver, ServiceRegistry


class AlphaService:
    def __init__(self) -> None:
        self.value = "alpha"


def test_registry_resolves_by_type_and_name() -> None:
    class AlphaAlias:
        pass

    registry = ServiceRegistry(by_type={}, by_alias={})
    alpha = registry.register(AlphaService(), aliases=["AlphaAlias"])

    assert registry.resolve(AlphaService) is alpha
    assert registry.resolve(AlphaAlias) is alpha


def test_dependency_resolver_injects_context_and_services() -> None:
    registry = ServiceRegistry(by_type={}, by_alias={})
    alpha = registry.register(AlphaService(), aliases=[])
    resolver = DependencyResolver(registry)

    def handler(alpha: AlphaService, extra: str) -> tuple[str, str]:
        return alpha.value, extra

    result = resolver.call(handler, {"extra": "context"})
    assert result == ("alpha", "context")


def test_dependency_resolver_errors_on_missing_dependency() -> None:
    registry = ServiceRegistry(by_type={}, by_alias={})
    resolver = DependencyResolver(registry)

    def handler(missing: AlphaService) -> str:
        return missing.value

    with pytest.raises(TypeError):
        resolver.call(handler, {})
