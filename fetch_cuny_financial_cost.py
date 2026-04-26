import asyncio
import json

from mcp.server.fastmcp import FastMCP, Context
from playwright.async_api import async_playwright
from pyotp import TOTP
from playwright.async_api import async_playwright
import asyncio
import dotenv
import tracemalloc

from test_cuny import handle_login_page, handle_otp_page, handle_financial_page

cuny_finance_mcp = FastMCP("cuny-finance-fetcher")


def get_otp():
    loc = dotenv.find_dotenv('.env')
    env = dotenv.load_dotenv(loc)
    secret = str(dotenv.get_key(loc, "CUNY_TOPT"))
    email = str(dotenv.get_key(loc, "CUNY_EMAIL"))
    password = str(dotenv.get_key(loc, "CUNY_PASSWORD"))
    otp = TOTP(secret)
    toptime = otp.now()
    return (email, password, toptime)


@cuny_finance_mcp.tool(
    description="A server that retrieves the cost of CUNY course per semester. it checks how much money you will pay for each semester, or how much money you owe.",
    title="Fetch Cuny Financial Cost",
    name="fetch_cuny_financial_cost"
)
async def fetch_cuny_financial_cost(
    ctx: Context,
    timeout: int = 30000,
) -> dict:
    """
    Fetch the financial cost of CUNY courses per semester by navigating CUNYFirst's
    student center and retrieving rendered HTML content after logging in.

    This asynchronous function uses Playwright to automate browser interactions,
    handles login with email, password, and OTP (one-time password), and extracts
    all relevant information regarding semester costs.

    :param ctx: Context instance for logging and runtime operation.
    :type ctx: Context
    :param timeout: Timeout value in milliseconds for waiting operations,
        such as loading pages or waiting for selectors.
    :type timeout: int
    :return: Dictionary containing the status of the fetch operation,
        the URL accessed, and either the rendered HTML or an error message.
    :rtype: dict
    """
    tracemalloc.start()
    url = "http://cunyfirst.cuny.edu/"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await browser.new_page()

        try:
            # Navigate and wait for JS/network to settle
            await page.goto(url, wait_until="networkidle", timeout=timeout)

            if "portaldown.cuny.edu" in page.url:
                return {"status": "error", "url": url, "error": "Portal is down"}
            email, password, otp = get_otp()
            await ctx.info(f"Logging in as {email}")
            await page.wait_for_selector("input[name=usernameDisplay]", timeout=timeout)

            await handle_login_page(page)
            await ctx.log("info", "Entering OTP...")
            await page.wait_for_selector(
                'input[placeholder="Enter TOTP"].oj-inputtext-input.oj-text-field-input.oj-component-initnode',
                timeout=timeout)

            await handle_otp_page(page)

            #student center
            await page.wait_for_selector("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$1']", timeout=timeout)
            await page.click("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$1']")

            #schedule builder
            await page.wait_for_selector("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$16']", timeout=timeout)

            await ctx.log("info","Going to check financial cost")
            #new_page_future = context.wait_for_event("page")
            await page.click("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$16']")

            #await new_page.evaluate("() => this.window.AS.openCourseBrowser();")

            await page.wait_for_load_state('networkidle')

            await ctx.log("info","Fetching costs")
            json_data = json.dumps(await handle_financial_page(page))


            return {
                "status": "success",
                "url": url,
                "json_length": len(json_data),
                "json": json_data
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
    cuny_finance_mcp.run()
