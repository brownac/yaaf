"""Generated service type aliases for consumers.

Do not edit by hand. Regenerate via `yaaf` CLI.
"""

from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from consumers.api.foo_bar_baz._service import Service as FooBarBazService
    from consumers.api.hello._service import Service as HelloService
    from consumers.api.users._service import Service as UsersService
else:
    class FooBarBazService:
        ...
    class HelloService:
        ...
    class UsersService:
        ...

class NameService(Protocol):
    ...

__all__ = ['FooBarBazService', 'HelloService', 'UsersService', 'NameService']

# Dynamic routes use Protocol stubs (invalid import paths).
