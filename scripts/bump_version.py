"""Update pyproject.toml to a calendar-based version with a timestamp.

Format: YYYY.MM.DD.HHMMSS (UTC)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    content = pyproject_path.read_text()
    stamp = datetime.now(timezone.utc).strftime("%Y.%m.%d.%H%M%S")

    lines = content.splitlines()
    in_project = False
    updated = False
    for idx, line in enumerate(lines):
        if line.strip() == "[project]":
            in_project = True
            continue
        if in_project and line.startswith("[") and line.strip() != "[project]":
            in_project = False
        if in_project and line.strip().startswith("version = "):
            lines[idx] = f'version = "{stamp}"'
            updated = True
            break

    if not updated:
        raise SystemExit("Could not find [project] version in pyproject.toml")

    pyproject_path.write_text("\n".join(lines) + "\n")
    print(stamp)


if __name__ == "__main__":
    main()
