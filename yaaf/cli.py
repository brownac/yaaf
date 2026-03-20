"""Command-line entrypoint for running the ASGI app."""

from __future__ import annotations

import argparse
import importlib
import uvicorn


def main() -> None:
    """CLI entrypoint for running a yaaf ASGI app."""
    parser = argparse.ArgumentParser(prog="yaaf", description="Run a yaaf ASGI app")
    parser.add_argument(
        "--app", default="yaaf.app:app", help="ASGI app path, e.g. module:app"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--root", default="api", dest="root_dir")

    args = parser.parse_args()

    if args.app == "yaaf.app:app":
        from .app import App

        app = App(root_dir=args.root_dir)
    else:
        module_path, app_name = args.app.split(":")
        module = importlib.import_module(module_path)
        app = getattr(module, app_name)

    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
