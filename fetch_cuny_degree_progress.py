import asyncio
import json

from mcp.server.fastmcp import FastMCP, Context
from playwright.async_api import async_playwright
from pyotp import TOTP
from playwright.async_api import async_playwright
import asyncio
import dotenv
import tracemalloc

from test_cuny import handle_login_page, handle_otp_page, handle_degreeworks_page

cuny_degree_mcp = FastMCP("cuny-degree-fetcher")


def get_otp():
    loc = dotenv.find_dotenv('.env')
    env = dotenv.load_dotenv(loc)
    secret = str(dotenv.get_key(loc, "CUNY_TOPT"))
    email = str(dotenv.get_key(loc, "CUNY_EMAIL"))
    password = str(dotenv.get_key(loc, "CUNY_PASSWORD"))
    otp = TOTP(secret)
    toptime = otp.now()
    return (email, password, toptime)


@cuny_degree_mcp.tool(
    description="A server that retrieves CUNY degree progress. It contains transcript, grades, and other academic information.",
    title="Fetch Cuny Degree Progress",
    name="fetch_cuny_degree_progress"
)
async def fetch_cuny_degree_progress(
    ctx: Context,
    timeout: int = 30000,
) -> dict:
    """
    Fetches the CUNY degree progress, including transcript, grades, and other academic
    information, by interacting with the web interface dynamically using Playwright.

    This function automates the login process, handles multi-factor authentication (MFA),
    navigates to the student's dashboard, and extracts the rendered HTML content to
    provide the requested academic details.

    :param ctx: The application context, used for logging information during execution.
                Assumes an object with a `log` method for log messages.
                Type: Context
    :param timeout: The time in milliseconds to wait for operations such as page navigation
                    or element selection before timing out. Defaults to 30000 (30 seconds).
                    Type: int
    :return: A dictionary containing the following keys:
             - "status": A string indicating the outcome ("success" or "error").
             - "url": The URL used for the operation.
             - "html_length": The length of the extracted HTML content if successful.
             - "html": The extracted HTML content if successful.
             - "error": A string description of the error, only present if the operation
               fails.
             Type: dict
    """
    tracemalloc.start()
    url = "https://degreeworks.cuny.edu/Dashboard_lc"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await browser.new_page()

        try:
            # Navigate and wait for JS/network to settle
            await page.goto(url, wait_until="networkidle", timeout=timeout)

            # Optional: wait for specific dynamic content to appear
            email, password, otp = get_otp()
            await ctx.info(f"Logging in as {email}")
            await page.wait_for_selector("input[name=usernameDisplay]", timeout=timeout)

            await handle_login_page(page)
            await ctx.log("info","Entering OTP...")
            await page.wait_for_selector('input[placeholder="Enter TOTP"].oj-inputtext-input.oj-text-field-input.oj-component-initnode', timeout=timeout)

            await handle_otp_page(page)

            degree_information = json.dumps(await handle_degreeworks_page(page))

            return {
                "status": "success",
                "url": url,
                "html_length": len(degree_information),
                "html": degree_information
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
    cuny_degree_mcp.run()
