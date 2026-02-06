"""Generate a consumers/api/__init__.py typing module from filesystem routes."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Protocol

HEADER = """\
\"\"\"Generated service type aliases for consumers.\n\nDo not edit by hand. Regenerate via `yaaf` CLI.\n\"\"\"\n\nfrom __future__ import annotations\n\nfrom typing import Any, Protocol, TYPE_CHECKING\n\n"""


def _is_identifier(segment: str) -> bool:
    return segment.isidentifier()


def _camel_case(parts: Iterable[str]) -> str:
    return "".join(
        sub[:1].upper() + sub[1:] for part in parts if part for sub in part.split("_") if sub
    )


def _strip_dynamic(segment: str) -> str:
    if segment.startswith("[") and segment.endswith("]"):
        return segment[1:-1]
    return segment


def _service_alias(route_parts: list[str]) -> str:
    normalized = [_strip_dynamic(part) for part in route_parts]
    safe_parts = [part for part in normalized if _is_identifier(part)]
    base = _camel_case(safe_parts) or "Route"
    return f"{base}Service"


def generate_services(consumers_dir: str = "consumers", output_path: str | None = None) -> Path:
    base = Path(consumers_dir)
    out_path = Path(output_path) if output_path else base / "api" / "__init__.py"

    if not base.exists():
        if not out_path.parent.exists():
            out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(HEADER + "\n__all__ = []\n")
        return out_path

    aliases: list[tuple[str, str]] = []
    dynamic_aliases: list[str] = []
    for root in base.rglob("_service.py"):
        if "api" not in root.parts:
            continue
        api_index = root.parts.index("api")
        route_parts = list(root.parts[api_index + 1 : -1])
        if any(part.startswith("[") and part.endswith("]") for part in route_parts):
            dynamic_aliases.append(_service_alias(route_parts))
            continue
        if not all(_is_identifier(part) for part in route_parts):
            continue
        module_path = ".".join([base.name, "api", *route_parts, "_service"])
        alias = _service_alias(route_parts)
        aliases.append((alias, module_path))

    aliases.sort(key=lambda item: item[0].lower())

    lines = [HEADER]
    lines.append("if TYPE_CHECKING:\n")
    if aliases:
        for alias, module_path in aliases:
            lines.append(f"    from {module_path} import Service as {alias}\n")
    else:
        lines.append("    pass\n")
    lines.append("else:\n")
    for alias, _ in aliases:
        lines.append(f"    class {alias}:\n        ...\n")

    for alias in dynamic_aliases:
        lines.append(f"\nclass {alias}(Protocol):\n    ...\n")

    exports = ", ".join([f"'{alias}'" for alias, _ in aliases] + [f"'{alias}'" for alias in dynamic_aliases])
    lines.append(f"\n__all__ = [{exports}]\n")

    if dynamic_aliases:
        lines.append("\n# Dynamic routes use Protocol stubs (invalid import paths).\n")

    if not out_path.parent.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines))
    return out_path
