import subprocess
import sys

from loguru import logger
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

system_mcp = FastMCP("filesystem-manager")

logger.remove()
logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])

@system_mcp.tool(
    title="Open File",
    description="Open a file",
    name="open_file"
)
async def open_file(path: str):
    query = f"open \"{path}\""
    subprocess.run(query, shell=True, text=True)
    return TextContent(type="text", text="file opened")

if __name__ == "__main__":
    system_mcp.run()
