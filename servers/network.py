import os
from pathlib import Path
from typing import Annotated

import requests
from PyPDF2 import PdfReader
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from playwright.async_api import async_playwright
from pydantic import Field

# Initialize MCP server
mcp = FastMCP("network")


@mcp.tool(
    title="Fetch Rendered HTML",
    description="A server that fetches html content of a webpage",
    name="fetch_rendered_html"
)
async def fetch_rendered_html(
        url: str,
        wait_for_selector: str | None = None,
        timeout: int = 30000
) -> dict:
    """
    Fetches and returns the fully rendered HTML content of a webpage.

    This function utilizes Playwright to render the page in a headless browser,
    allowing it to capture content from dynamic pages. Users can optionally wait
    for a specific DOM selector to appear before extracting the HTML.

    :param url: The URL of the webpage to fetch.
    :type url: str

    :param wait_for_selector: Optional CSS selector to wait for before fetching
        the webpage's content, allowing dynamic page elements to load.
    :type wait_for_selector: str | None

    :param timeout: Time in milliseconds to wait for page load and optional
        selector appearance. Defaults to 30000 (30 seconds).
    :type timeout: int

    :return: A dictionary containing the operation status, the URL of the
        webpage, the length of the fetched HTML content, and the rendered HTML.
        If an error occurs, returns a dictionary with the status and error details.
    :rtype: dict
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=os.getcwd(),
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-infobars',
                '--disable-extensions',
            ],
            # Realistic browser fingerprint
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            # Bypass CSP & other restrictions
            bypass_csp=True,
        )
        page = await browser.new_page()

        try:
            # Navigate and wait for JS/network to settle
            await page.goto(url, wait_until="networkidle", timeout=timeout)

            # Optional: wait for specific dynamic content to appear
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=timeout)

            # Extract fully rendered HTML
            html = await page.content()

            return {
                "status": "success",
                "url": url,
                "html_length": len(html),
                "html": html
            }

        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
        finally:
            await browser.close()


@mcp.tool(
    title="Download File",
    description="Downloads a file from a URL to cwd, when finished downloading if file is pdf should call read_pdf",
    name="download_file"
)
async def download_file(
        url: str,
        filename: str
) -> dict:
    """
    Downloads a file from the given URL and saves it to /tmp/mcp-fs/downloads.

    :param url: The URL of the file to download.
    :type url: str

    :param filename: The name to save the file as.
    :type filename: str

    :return: A dictionary containing the operation status, download path, and file size.
        If an error occurs, returns a dictionary with the status and error details.
    :rtype: dict
    """
    try:
        # Create download directory if it doesn't exist
        download_dir = Path(".")
        download_dir.mkdir(parents=True, exist_ok=True)

        # Full path for the downloaded file
        file_path = download_dir / filename

        # Download the file
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()

        # Write the file to disk
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        file_size = file_path.stat().st_size

        return {
            "status": "success",
            "url": url,
            "download_path": str(file_path),
            "file_size": file_size,
            "$hint": "if the file is a pdf, call read_pdf"
        }

    except Exception as e:
        return {
            "status": "error",
            "url": url,
            "error": str(e)
        }


@mcp.tool(
    name="read_pdf",
    description=(
            "Read and extract text content from a PDF file. "
            "Returns all text from the PDF as a UTF-8 string."
    ),
)
def read_pdf(
        path: Annotated[
            str,
            Field(
                description=(
                        "Path to the PDF file, relative to the server root. "
                        "Example: 'documents/report.pdf'"
                )
            ),
        ],
        join: Annotated[
            bool,
            Field(
                description=(
                    "If True, join all extracted text into a single string. "
                    "If False, return a list of strings, one for each page."
                )
            )
        ] = True
) -> str | list[str]:
    """Extract and return all text content from the PDF file at *path*."""
    p = Path(path).resolve()
    if not p.exists():
        raise ToolError(f"File not found: '{path}'")
    if not p.is_file():
        raise ToolError(f"'{path}' is not a file.")
    if p.suffix.lower() != ".pdf":
        raise ToolError(f"'{path}' is not a PDF file.")

    try:
        reader = PdfReader(str(p))
        text_content = []
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_content.append(f"--- Page {page_num} ---\n{page_text}")

        if not text_content:
            return f"PDF '{path}' contains no extractable text."

        return "\n\n".join(text_content) if join else text_content
    except Exception as e:
        raise ToolError(f"Failed to read PDF '{path}': {str(e)}")

if __name__ == "__main__":
    # Runs MCP server over stdio by default
    mcp.run()
