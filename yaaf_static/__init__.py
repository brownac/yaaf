"""Static file serving for yaaf."""

from __future__ import annotations

from pathlib import Path

from yaaf import Response
from yaaf.types import Params


MIME_TYPES: dict[str, str] = {
    ".aac": "audio/aac",
    ".abw": "application/x-abiword",
    ".arc": "application/x-freearc",
    ".avif": "image/avif",
    ".avi": "video/x-msvideo",
    ".azw": "application/vnd.amazon.ebook",
    ".bin": "application/octet-stream",
    ".bmp": "image/bmp",
    ".bz": "application/x-bzip",
    ".bz2": "application/x-bzip2",
    ".cda": "application/x-cdf",
    ".csh": "application/x-csh",
    ".css": "text/css",
    ".csv": "text/csv",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".eot": "application/vnd.ms-fontobject",
    ".epub": "application/epub+zip",
    ".gz": "application/gzip",
    ".gif": "image/gif",
    ".htm": "text/html",
    ".html": "text/html",
    ".ico": "image/x-icon",
    ".ics": "text/calendar",
    ".jar": "application/java-archive",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".js": "text/javascript",
    ".json": "application/json",
    ".jsonld": "application/ld+json",
    ".mid": "audio/midi",
    ".midi": "audio/midi",
    ".png": "image/png",
    ".pdf": "application/pdf",
    ".php": "application/x-httpd-php",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".rar": "application/vnd.rar",
    ".rtf": "application/rtf",
    ".sh": "application/x-sh",
    ".svg": "image/svg+xml",
    ".tar": "application/x-tar",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".ts": "video/mp2t",
    ".ttf": "font/ttf",
    ".txt": "text/plain",
    ".vsd": "application/vnd.visio",
    ".wav": "audio/wav",
    ".weba": "audio/webm",
    ".webm": "video/webm",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".xhtml": "application/xhtml+xml",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xml": "application/xml",
    ".xul": "application/vnd.mozilla.xul+xml",
    ".zip": "application/zip",
    ".3gp": "video/3gpp",
    ".3g2": "video/3gpp2",
    ".7z": "application/x-7z-compressed",
}


class StaticHandler:
    """Handler that serves static files from a directory."""

    def __init__(self, directory: str, index: str = "index.html") -> None:
        self.directory = Path(directory).resolve()
        self.index = index

    def __call__(self, path_params: Params | None = None) -> Response:
        if path_params is None:
            path_params = {}
        filepath = path_params.get("filepath", self.index)

        if ".." in filepath or filepath.startswith("/"):
            return Response.text("Forbidden", status=403)

        # Normalize path separators for comparison
        file_path = self.directory / filepath

        # Security: ensure resolved path is within the static directory
        try:
            resolved = file_path.resolve()
            # Normalize both paths to use the same separator for comparison
            base_parts = self.directory.parts
            resolved_parts = resolved.parts
            # Check if resolved path starts with base path
            if not (
                resolved_parts == base_parts
                or resolved_parts[: len(base_parts)] == base_parts
            ):
                return Response.text("Forbidden", status=403)
        except (ValueError, OSError):
            return Response.text("Not Found", status=404)

        if file_path.is_dir():
            file_path = file_path / self.index

        if not file_path.exists() or not file_path.is_file():
            return Response.text("Not Found", status=404)

        content_type = MIME_TYPES.get(
            file_path.suffix.lower(), "application/octet-stream"
        )
        return Response(
            file_path.read_bytes(),
            headers=[("Content-Type", content_type)],
        )


def static_files(directory: str, index: str = "index.html") -> StaticHandler:
    """Create a static file handler for a directory.

    Args:
        directory: Root directory to serve files from.
        index: Default file to serve when path points to a directory.

    Returns:
        A StaticHandler instance that serves files at the configured route.

    Example:
        # api/static/[...filepath]/_server.py
        # Serves files at /static/* from the "public" directory
        from yaaf_static import static_files

        async def get(params=static_files("public")):
            return params
    """
    return StaticHandler(directory, index)
