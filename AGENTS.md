# AGENTS.md - yaaf Contributor Guide

> **Note**: This file is for AI agents working on the yaaf codebase.
> For human documentation, see [README.md](./README.md).

---

## Project Overview

**yaaf** = "Yet Another ASGI Framework"

A minimal Python ASGI web framework with filesystem-first routing. Routes are discovered from the directory structure under `consumers/**/api` rather than declared with decorators.

### Quick Facts
- **Language**: Python >= 3.13
- **Dependencies**: `uvicorn>=0.23`
- **Package Name**: `yaafcli` (in PyPI)
- **CLI Entry**: `yaaf` command
- **Test Framework**: pytest + pytest-asyncio

---

## Architecture

### Core Modules

| File | Purpose |
|------|---------|
| `yaaf/app.py` | Main ASGI App class, Request dataclass, HTTP request handling |
| `yaaf/loader.py` | Filesystem route discovery, module loading, pattern building |
| `yaaf/di.py` | Dependency injection (ServiceRegistry, DependencyResolver, @service decorator) |
| `yaaf/cli.py` | CLI entrypoint |
| `yaaf/responses.py` | Response class (text, json methods), as_response() normalizer |
| `yaaf/types.py` | Type aliases (ASGIScope, ASGIReceive, ASGISend, Params, Handler) |

### Request Flow

```
ASGI Request
    ↓
App.__call__() [app.py]
    ↓
discover_routes() [loader.py] - finds routes from filesystem
    ↓
DependencyResolver.call() [di.py] - injects request, params, services
    ↓
Handler function [_server.py] - returns ResponseLike
    ↓
as_response() [responses.py] - normalizes to Response
    ↓
Response.send() - sends to ASGI client
```

---

## Key Patterns

### 1. Route Structure

Routes live under `consumers/**/api/`. Each route directory requires:

```
consumers/api/<route>/
    _server.py   # Handler functions (required)
    _service.py  # Service class (optional)
```

**Dynamic Routes**: Use `[param]` naming:
```
consumers/api/users/[id]/_server.py  →  route: /api/users/<id>
```

**Example Structure**:
```
consumers/
  api/
    hello/
      _server.py    → GET /api/hello
      _service.py
    users/
      _server.py    → GET /api/users, /api/users/<id>
      _service.py
    name_dynamic/
      _server.py    → GET /api/<name>
      _service.py
```

### 2. Handler Pattern (`_server.py`)

Export lowercase HTTP method functions. Import services directly from their source modules:

```python
from yaaf import Request
from yaaf.types import Params
from consumers.api.hello._service import HelloService  # Direct import

async def get(request: Request, service: HelloService, params: Params) -> dict:
    """Handler for GET requests."""
    return {"message": service.message(), "path": request.path}

async def post(request: Request, service: HelloService) -> dict:
    """Handler for POST requests."""
    return {"status": "created"}
```

**For Dynamic Routes**: Use direct imports (directory names must be valid Python identifiers):
```python
# consumers/api/name_dynamic/_server.py
from yaaf.types import Params
from consumers.api.name_dynamic._service import NameService

async def get(params: Params, service: NameService) -> dict:
    return {"message": service.greet(params["name"])}
```

**Supported HTTP Methods**: `get`, `post`, `put`, `delete`, `patch`, `options`, `head`

**Injectable Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `request` | `Request` | yaaf Request object (scope, body, path_params) |
| `params` | `Params` | dict of dynamic route parameters |
| `path_params` | `Params` | alias for `params` |
| `<service>` | Any | Auto-injected by type annotation |

### 3. Service Pattern (`_service.py`)

Use the `@service` decorator to mark and register services:

```python
from yaaf import service

@service("MyService", aliases=["ms"])
class MyService:
    def __init__(self) -> None:
        self._value = "hello"
    
    def message(self) -> str:
        return self._value

# Required export name
service = MyService
```

**Decorator Options**:
| Option | Type | Description |
|--------|------|-------------|
| `name` | `str` | Custom name for DI resolution (defaults to class name) |
| `aliases` | `list[str]` | Additional names to resolve by |

**Service Dependencies**: Services can depend on other services via constructor injection:

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
from consumers.api.users._service import UsersService  # Direct import

@service("HelloService")
class HelloService:
    def __init__(self, users: UsersService) -> None:
        self._users = users
    
    def message(self) -> str:
        user = self._users.get_user("1")
        return f"Hello, {user['name']}"

service = HelloService
```

service = Service  # Callable class, DI will instantiate
```

### 4. Response Types

Handlers can return multiple types (normalized by `as_response()`):

| Return Type | Behavior |
|-------------|----------|
| `Response` | Used as-is |
| `str` | `Response.text()` with 200 |
| `bytes` | `Response` with `application/octet-stream` |
| `dict` / `list` | `Response.json()` |
| `tuple(body, status)` | Body as above with custom status |

### 5. Type Checking

Import services directly from their source modules. Directory names must be valid Python identifiers:

```python
# Direct import from service module
from consumers.api.hello._service import HelloService
```

---

## Dependency Injection System

### @service Decorator

Use `@service` to mark classes as injectable services:

```python
from yaaf import service

@service("MyService", aliases=["ms"])
class MyService:
    def do_something(self) -> str:
        return "done"

service = MyService
```

**Options**:
- `name`: Custom DI name (defaults to class name)
- `aliases`: Additional names to resolve by

### ServiceRegistry

Stores services by type and aliases:

```python
@dataclass
class ServiceRegistry:
    by_type: dict[type[Any], Any]      # Direct type matches
    by_alias: dict[str, Any]          # Name-based lookups
```

### DependencyResolver

Resolves function arguments from context or registry:

1. Check context first (`request`, `params`, `path_params`)
2. Try registry by type annotation
3. Try registry by base class/protocol
4. Try registry by `__name__`
5. Use default value if available
6. Raise `TypeError` if unresolved

### Circular Dependency Handling

The loader uses iterative resolution:
```python
while unresolved:
    # Try to resolve each service
    # If stuck, raise RuntimeError with missing deps
```

---

## Route Matching

### Pattern Building

```python
build_pattern(["users", "[id]"], prefix="api")
# Returns:
#   pattern: "^/api/users/([^/]+)$"
#   param_names: ["id"]
#   static_count: 1
#   segment_count: 2
```

### Static vs Dynamic Precedence

Routes are sorted so **static routes win**:
```python
routes.sort(key=lambda r: (r.static_count, r.segment_count), reverse=True)
```

**Warning**: If a dynamic route would match a static route:
```
Warning: dynamic route /api/[name] matches static route /api/hello
```

---

## Testing Patterns

### Test Structure

Tests use pytest with tmp_path for isolation:

```python
@pytest.mark.asyncio
async def test_example(tmp_path: Path) -> None:
    # Create consumer structure
    base = tmp_path / "consumers" / "api" / "test"
    base.mkdir(parents=True)
    
    # Write files
    (base / "_service.py").write_text("class Service:...\nservice = Service()")
    (base / "_server.py").write_text("async def get(): return 'ok'")
    
    # Test
    app = App(consumers_dir=str(tmp_path / "consumers"))
    # ...
```

### Dummy ASGI Objects

```python
class DummySend:
    messages: list[dict] = []
    async def __call__(self, message: dict) -> None:
        self.messages.append(message)

class DummyReceive:
    async def __call__(self) -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}
```

### Running Tests

```bash
# All tests
pytest tests/

# Specific file
pytest tests/test_app_integration.py

# With verbose output
pytest tests/ -v
```

---

## CLI Commands

```bash
yaaf [--app module:app] [--host HOST] [--port PORT] [--reload] [--consumers-dir DIR]
```

---

## Versioning

Calendar-based: `YYYY.MM.DD.HHMMSS` (UTC)

```bash
python scripts/bump_version.py
```

---

## Contributing Guidelines

### Code Style
- Use `from __future__ import annotations` for all files
- Type hints required for all public functions
- Use dataclasses for data structures
- Async/await for all handler functions

### Naming Conventions
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Private: `_leading_underscore`
- Constants: `SCREAMING_SNAKE_CASE`

### Adding New Features

1. **New HTTP Method**: Add to handler list in `loader.py`:
   ```python
   for method in ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "YOUR_NEW_METHOD"):
   ```

2. **New Response Type**: Add to `as_response()` in `responses.py`

3. **New CLI Command**: Add subparser in `cli.py`

### Testing Requirements
- All new features require tests
- Tests must pass before PR merge
- Run: `pytest tests/ -v`

---

## File Checklist for New Route

To add a new route `/api/my-resource/<id>`:

- [ ] Create `consumers/api/my-resource/[id]/_server.py`
- [ ] Create `consumers/api/my-resource/[id]/_service.py`
- [ ] Export `async def get|post|etc()` in `_server.py`
- [ ] Export `service` (instance or class) in `_service.py`
- [ ] Import service types from `consumers.api`
- [ ] Run `yaaf gen-services` (or use `yaaf` CLI)
- [ ] Add tests in `tests/`

---

## Common Patterns

### Simple Handler (No Service)
```python
# consumers/api/status/_server.py
from yaaf import Request

async def get(request: Request) -> dict:
    return {"status": "ok"}
```

### Handler with Service
```python
# consumers/api/greet/_server.py
from yaaf import Request
from yaaf.types import Params
from consumers.api import GreetService

async def get(request: Request, params: Params, service: GreetService) -> dict:
    name = params.get("name", "World")
    return {"message": service.greet(name)}
```

### Handler Returning Different Status
```python
async def post(request: Request, service: MyService) -> tuple[dict, int]:
    return {"error": "invalid"}, 400
```

### Service with Multiple Dependencies
```python
# consumers/api/reports/_service.py
from consumers.api import DatabaseService, CacheService

class Service:
    def __init__(self, db: DatabaseService, cache: CacheService) -> None:
        self._db = db
        self._cache = cache
    
    def get_report(self, id: str) -> dict:
        cached = self._cache.get(id)
        if cached:
            return cached
        return self._db.fetch_report(id)

service = Service
```

---

## Key Design Decisions

1. **Filesystem Routing**: Makes routes discoverable by directory inspection
2. **Explicit Files**: `_server.py` and `_service.py` separation for clarity
3. **Lazy DI**: Services injected only when needed
4. **Static Precedence**: Prevents accidental dynamic route shadowing
5. **Minimal Core**: No built-in auth/middleware - intentionally left for users

---

## References

- [README.md](./README.md) - Human-readable documentation
- [pyproject.toml](./pyproject.toml) - Package configuration
- [pytest.ini](./pytest.ini) - Test configuration
