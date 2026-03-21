# yaaf

YAAF stands for "Yet Another ASGI Framework".

A minimal Python ASGI app scaffold that discovers routes from the filesystem. It includes a tiny router and a CLI wrapper around `uvicorn`.

## Design Goals and Opinions

- **Filesystem-first routing.** Routes are inferred from the `api/` directory structure rather than declared with decorators. This keeps routing discoverable by looking at the tree.
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

- `GET /hello`
- `GET /<name>` (dynamic segment)

## Routing Model

Routes are inferred from the `api/` directory structure.

- Every route directory must contain `_server.py` and `_service.py`.
- The route path is `/...` plus the sub-path under `api/`.
- Dynamic segments use `[param]` directory names and are exposed as `params`/`path_params`.
- Catch-all segments use `[...filepath]` for multi-segment paths.

Example layout:

```text
api/
  users/
    [id]/
      _server.py
      _service.py
    _server.py
    _service.py
  hello/
    _server.py
    _service.py
  [name]/
    _server.py
    _service.py
```

## Services (`_service.py`)

Use the `@service` decorator to mark and register services:

```python
from yaaf import service


@service("UsersService")
class UsersService:
    def get_user(self, user_id: str) -> dict:
        return {"id": user_id, "name": "User"}


service = UsersService
```

**Decorator Options**:
- `name`: Custom service name for DI resolution (defaults to class name)
- `aliases`: Additional names to resolve by

## Handlers (`_server.py`)

Export lowercase HTTP method functions. Import services directly from their source modules:

```python
from yaaf import Request
from yaaf.types import Params
from api.users._service import UsersService


async def get(request: Request, params: Params, service: UsersService) -> dict:
    user_id = params.get("id", "1")
    return service.get_user(user_id)
```

**Injectable Parameters**:
- `request` gives you the `yaaf.Request` object
- `params` or `path_params` provides dynamic route parameters
- Services are injected by type annotations

## Service Dependencies

Services can depend on other services via constructor injection:

```python
# users/_service.py
from yaaf import service


@service("UsersService")
class UsersService:
    def get_user(self, user_id: str) -> dict:
        return {"id": user_id, "name": "User"}


service = UsersService
```

```python
# hello/_service.py
from yaaf import service
from api.users._service import UsersService


@service("HelloService")
class HelloService:
    def __init__(self, users: UsersService) -> None:
        self._users = users

    def message(self) -> str:
        user = self._users.get_user("1")
        return f"Hello, {user['name']}"


service = HelloService
```

## Static File Serving

Use `yaaf_static` to serve files from a directory:

```python
# api/static/[...filepath]/_server.py
from yaaf.types import Params
from yaaf_static import static_files

async def get(path_params: Params, static=static_files("public")):
    return static(path_params)
```

The `static_files()` function returns a handler that:
- Serves files relative to the specified directory
- Returns 404 if file not found
- Blocks path traversal attacks (`../`)

## Running Another App

```bash
yaaf --app your_package.app:app
```

## Versioning

This project uses calendar-based versions with a timestamp (UTC). To bump the version:

```bash
python scripts/bump_version.py
```
