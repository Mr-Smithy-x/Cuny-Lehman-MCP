import asyncio
from mcp.server.fastmcp import FastMCP, Context
from playwright.async_api import async_playwright
from pyotp import TOTP
from playwright.async_api import async_playwright
import asyncio
import dotenv
import tracemalloc


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
    tracemalloc.start()
    url = "http://cunyfirst.cuny.edu/"
    """
    Fetch fully JavaScript-rendered HTML from a URL.
    Returns a dict with status, html, and metadata for better AI parsing.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await browser.new_page()

        try:
            # Navigate and wait for JS/network to settle
            await page.goto(url, wait_until="networkidle", timeout=timeout)

            # Optional: wait for specific dynamic content to appear
            await ctx.log("info","Logging in...")
            await page.wait_for_selector("input[name=usernameDisplay]", timeout=timeout)

            email, password, otp = get_otp()

            await page.fill("input[name=usernameDisplay]", email)
            await page.fill("input[name=password]", password)
            await page.click("button[type=submit]")


            await ctx.log("info","Entering OTP...")
            await page.wait_for_selector('input[placeholder="Enter TOTP"].oj-inputtext-input.oj-text-field-input.oj-component-initnode', timeout=timeout)

            email, password, otp = get_otp()

            await ctx.log("info","Logging in as {}".format(email))
            await page.fill('input[placeholder="Enter TOTP"].oj-inputtext-input.oj-text-field-input.oj-component-initnode', otp)
            await page.wait_for_selector("button[class=oj-button-button]", timeout=timeout)
            await page.click("button[class=oj-button-button]")

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
            html = await page.inner_html("div[id='PT_MAIN']")
            #html = await new_page.inner_html('div[id="requirements"]')

            # Extract fully rendered HTML
            #html = await page.content()
            screenshot = await page.screenshot(path="screenshot.png")


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
    cuny_finance_mcp.run()
