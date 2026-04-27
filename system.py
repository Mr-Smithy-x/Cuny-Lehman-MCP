import subprocess
import sys
from pathlib import Path
from typing import Annotated
import os
import shutil
from loguru import logger
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import TextContent
from pydantic import Field

# ── Server instantiation ──────────────────────────────────────────────────────
system_mcp = FastMCP(
    name="filesystem",
    instructions=(
        "A filesystem server. All paths must be absolute and must remain within "
        "the allowed root directory. Raises errors on path traversal attempts."
    ),
)


logger.remove()
logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])

@system_mcp.tool(
    title="Open file",
    description="Open a file, if the file contains a path starting with \\Users then we know that its on the active users directory otherwise it will check the mcp root directory.",
    name="open_file"
)
async def open_file(path: str):
    if Path(path).exists():
        query = f"open \"{path}\""
    elif Path(safe_path(path)).exists():
        query = f"open \"{safe_path(path)}\""
    else:
        raise FileNotFoundError(f"File not found: {path}")

    subprocess.run(query, shell=True, text=True)
    return TextContent(type="text", text="file opened")

"""
Filesystem MCP Server using FastMCP.

Provides tools for reading, writing, listing, and managing files
on the local filesystem with proper path safety checks.
"""


# ── Configurable root (override via env var) ──────────────────────────────────
ROOT: Path = Path(os.environ.get("FS_ROOT", "/tmp/mcp-fs")).resolve()
ROOT.mkdir(parents=True, exist_ok=True)


# ── Safety helper ─────────────────────────────────────────────────────────────
def safe_path(raw: str) -> Path:
    """Resolve and validate that a path stays within ROOT."""
    resolved = (ROOT / raw.lstrip("/")).resolve()
    if not str(resolved).startswith(str(ROOT)):
        raise ToolError(f"Path traversal denied: '{raw}' escapes the root.")
    return resolved


# ── Resources ─────────────────────────────────────────────────────────────────
@system_mcp.resource(
    uri="filesystem://root",
    name="Root directory",
    description="The absolute path of the allowed filesystem root.",
    mime_type="text/plain",
)
def root_resource() -> str:
    """Return the root directory that this server operates within."""
    return str(ROOT)

# ── Tools ─────────────────────────────────────────────────────────────────────
@system_mcp.tool(
    name="read_file",
    description=(
        "Read the full text content of a file. "
        "Returns the file content as a UTF-8 string."
    ),
)
def read_file(
    path: Annotated[
        str,
        Field(
            description=(
                "Path to the file, relative to the server root. "
                "Example: 'reports/q1.txt'"
            )
        ),
    ],
) -> str:
    """Return the text content of the file at *path*."""
    p = safe_path(path)
    if not p.exists():
        raise ToolError(f"File not found: '{path}'")
    if not p.is_file():
        raise ToolError(f"'{path}' is not a file.")
    return p.read_text(encoding="utf-8")


@system_mcp.tool(
    name="write_file",
    description=(
        "Write (or overwrite) a file with the given text content. "
        "Creates parent directories automatically. Returns a confirmation message."
    ),
)
def write_file(
    path: Annotated[
        str,
        Field(description="Destination path relative to the server root."),
    ],
    content: Annotated[
        str,
        Field(description="Text content to write into the file (UTF-8)."),
    ],
    overwrite: Annotated[
        bool,
        Field(description="If False and the file already exists, raise an error."),
    ] = True,
) -> str:
    """Write *content* to *path*, optionally refusing to overwrite existing files."""
    p = safe_path(path)
    if p.exists() and not overwrite:
        raise ToolError(
            f"'{path}' already exists and overwrite=False."
        )
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to '{path}'."


@system_mcp.tool(
    name="list_directory",
    description=(
        "List the contents of a directory. "
        "Returns a newline-separated list of names; directories are suffixed with '/'."
    ),
)
def list_directory(
    path: Annotated[
        str,
        Field(
            description=(
                "Directory path relative to the server root. "
                "Use '.' or '' for the root itself."
            )
        ),
    ] = ".",
) -> str:
    """Return directory contents as a formatted list."""
    p = safe_path(path)
    if not p.exists():
        raise ToolError(f"Directory not found: '{path}'")
    if not p.is_dir():
        raise ToolError(f"'{path}' is not a directory.")

    entries = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name))
    lines = [f"{e.name}/" if e.is_dir() else e.name for e in entries]
    return "\n".join(lines) if lines else "(empty directory)"


@system_mcp.tool(
    name="delete_file",
    description="Permanently delete a single file. Does NOT delete directories.",
)
def delete_file(
    path: Annotated[
        str,
        Field(description="Path to the file to delete, relative to the server root."),
    ],
) -> str:
    """Delete the file at *path*."""
    p = safe_path(path)
    if not p.exists():
        raise ToolError(f"File not found: '{path}'")
    if not p.is_file():
        raise ToolError(f"'{path}' is not a file. Use delete_directory to remove dirs.")
    p.unlink()
    return f"Deleted '{path}'."


@system_mcp.tool(
    name="delete_directory",
    description=(
        "Delete a directory and all its contents recursively. "
        "Use with caution — this is irreversible."
    ),
)
def delete_directory(
    path: Annotated[
        str,
        Field(description="Path to the directory to delete, relative to the server root."),
    ],
    confirm: Annotated[
        bool,
        Field(
            description=(
                "Must be True to proceed. Acts as a confirmation guard "
                "against accidental deletion."
            )
        ),
    ] = False,
) -> str:
    """Recursively remove *path* after checking the *confirm* flag."""
    if not confirm:
        raise ToolError(
            "Set confirm=True to acknowledge that deletion is irreversible."
        )
    p = safe_path(path)
    if not p.exists():
        raise ToolError(f"Directory not found: '{path}'")
    if not p.is_dir():
        raise ToolError(f"'{path}' is not a directory.")
    if p == ROOT:
        raise ToolError("Deleting the server root is not allowed.")
    shutil.rmtree(p)
    return f"Deleted directory '{path}' and all its contents."


@system_mcp.tool(
    name="move",
    description="Move or rename a file or directory.",
)
def move(
    source: Annotated[
        str,
        Field(description="Source path relative to the server root."),
    ],
    destination: Annotated[
        str,
        Field(description="Destination path relative to the server root."),
    ],
) -> str:
    """Move *source* to *destination*."""
    src = safe_path(source)
    dst = safe_path(destination)
    if not src.exists():
        raise ToolError(f"Source not found: '{source}'")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return f"Moved '{source}' → '{destination}'."


@system_mcp.tool(
    name="file_info",
    description=(
        "Return metadata about a file or directory: "
        "size (bytes), last-modified time, and type."
    ),
)
def file_info(
    path: Annotated[
        str,
        Field(description="Path relative to the server root."),
    ],
) -> dict:
    """Return a metadata dict for the entry at *path*."""
    p = safe_path(path)
    if not p.exists():
        raise ToolError(f"Path not found: '{path}'")
    stat = p.stat()
    return {
        "path": str(p.relative_to(ROOT)),
        "type": "directory" if p.is_dir() else "file",
        "size_bytes": stat.st_size,
        "modified": stat.st_mtime,
    }


# ── Prompts ───────────────────────────────────────────────────────────────────
@system_mcp.prompt(
    name="summarise_file",
    description="Generate a prompt that asks the LLM to summarise a file's contents.",
)
def summarise_file(
    path: Annotated[
        str,
        Field(description="Path to the file to summarise, relative to the server root."),
    ],
) -> str:
    """Return a ready-to-send prompt string for summarising *path*."""
    content = read_file(path)          # re-use the tool logic
    return (
        f"Please provide a concise summary of the following file ('{path}'):\n\n"
        f"{content}"
    )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    system_mcp.run()           # defaults to stdio transport
    # For SSE (HTTP) transport:  mcp.run(transport="sse", host="0.0.0.0", port=8000)