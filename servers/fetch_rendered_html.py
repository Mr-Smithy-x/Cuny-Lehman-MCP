from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

# Initialize MCP server
mcp = FastMCP("rendered-html-fetcher")


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
    mcp.run()
