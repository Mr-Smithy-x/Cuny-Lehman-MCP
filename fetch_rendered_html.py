from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

# Initialize MCP server
html_mcp = FastMCP("rendered-html-fetcher")


@html_mcp.tool(
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
    Fetch fully JavaScript-rendered HTML from a URL.
    Returns a dict with status, html, and metadata for better AI parsing.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
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

if __name__ == "__main__":
    # Runs MCP server over stdio by default
    html_mcp.run()
