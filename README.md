# yaaf

YAAF stands for "Yet Another ASGI Framework".

A minimal Python ASGI app scaffold that discovers routes from the filesystem. It includes a tiny router and a CLI wrapper around `uvicorn`.

## Design Goals and Opinions

- **Filesystem-first routing.** Routes are inferred from the directory structure under `consumers/**/api` rather than declared with decorators. This keeps routing discoverable by looking at the tree.
- **Explicit endpoint files.** Each route has `_server.py` and `_service.py` to separate request handling from domain logic.
- **Dependency injection without wiring.** Services are registered automatically and injected by name/type, so handlers and services focus on behavior, not setup.
- **Static-first routing precedence.** Static routes always win over dynamic segments, with warnings when a dynamic route would overlap a static route.
- **Minimal core.** The framework is intentionally small and opinionated, leaving room for you to add auth, middleware, validation, etc.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Run the built-in example routes
yaaf --reload
```

Example routes:

- `GET /api/hello`
- `GET /api/<name>` (dynamic segment)

## Routing Model

Routes are inferred from the directory structure under any `consumers/**/api` directory.

- Every route directory must contain `_server.py` and `_service.py`.
- The route path is `/api/...` plus the sub-path after `api/`.
- Dynamic segments use `[param]` directory names and are exposed as `params`/`path_params`.

Example layout:

```text
consumers/
  api/
    users/
      _server.py
      _service.py
    hello/
      _server.py
      _service.py
    [name]/
      _server.py
      _service.py
```

## Handlers and Services

In `_server.py`, export functions named after HTTP methods (lowercase): `get`, `post`, etc. The function signature is resolved via dependency injection:

- `request` gives you the `yaaf.Request` object.
- `params` or `path_params` provides dynamic route parameters.
- Services are injected by type annotations.

Example `_server.py`:

```python
from consumers.services import HelloService
from yaaf import Request
from yaaf.types import Params


async def get(request: Request, service: HelloService, params: Params):
    return {"message": service.message(), "path": request.path, "params": params}
```

In `_service.py`, expose a module-level `service` instance (or a callable like `Service` or `get_service`). Services are registered and can be injected into other services or handlers:

```python
from consumers.services import UsersService


class Service:
    def __init__(self, users: UsersService) -> None:
        self._users = users

    def message(self) -> str:
        user = self._users.get_user("1")
        return f"Hello from yaaf, {user['name']}"

service = Service
```

## Service-to-Service Injection

Services can depend on other services via type annotations. Example layout:

```text
consumers/
  api/
    users/
      _service.py
      _server.py
    hello/
      _service.py
      _server.py
```

`consumers/api/users/_service.py`
```python
class Service:
    def get_user(self, user_id: str) -> dict:
        return {"id": user_id, "name": "Austin"}

service = Service()
```

`consumers/api/hello/_service.py`
```python
from yaaf.services import UsersService


class Service:
    def __init__(self, users: UsersService) -> None:
        self._users = users

    def message(self) -> str:
        user = self._users.get_user("1")
        return f"Hello from yaaf, {user['name']}"

service = Service
```

`consumers/api/hello/_server.py`
```python
from consumers.services import HelloService
from yaaf import Request


async def get(request: Request, service: HelloService):
    return {"message": service.message(), "path": request.path}
```

## Running Another App

```bash
yaaf --app your_package.app:app
```

## Versioning

This project uses calendar-based versions with a timestamp (UTC). To bump the version:

```bash
python scripts/bump_version.py
```

## Service Type Generation

Every `yaaf` command regenerates `consumers/services.py` for type-checking. You can also run it explicitly:

```bash
yaaf gen-services
```

Dynamic route segments like `[name]` get Protocol stubs in the generated file since they are not valid import paths.
