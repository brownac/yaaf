"""Command-line entrypoint for running the ASGI app."""

from __future__ import annotations

import argparse
import sys
import uvicorn

from .gen_services import generate_services


def main() -> None:
    """CLI entrypoint for running a yaaf ASGI app."""
    parser = argparse.ArgumentParser(prog="yaaf", description="Run a yaaf ASGI app")
    subparsers = parser.add_subparsers(dest="command")
    parser.set_defaults(command="serve")

    serve_parser = subparsers.add_parser("serve", help="Run the ASGI server")
    serve_parser.add_argument("--app", default="yaaf.app:app", help="ASGI app path, e.g. module:app")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", default=8000, type=int)
    serve_parser.add_argument("--reload", action="store_true")
    serve_parser.add_argument("--consumers-dir", default="consumers")
    serve_parser.set_defaults(command="serve")

    gen_parser = subparsers.add_parser("gen-services", help="Generate consumers/services.py")
    gen_parser.add_argument("--consumers-dir", default="consumers")
    gen_parser.add_argument("--output", default=None)
    gen_parser.set_defaults(command="gen-services")

    if len(sys.argv) > 1 and sys.argv[1] == "gen-services":
        args = parser.parse_args()
    else:
        args = parser.parse_args(["serve", *sys.argv[1:]])

    if args.command == "gen-services":
        generate_services(consumers_dir=args.consumers_dir, output_path=args.output)
        return

    generate_services(consumers_dir=args.consumers_dir)
    uvicorn.run(args.app, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
