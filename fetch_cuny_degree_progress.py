import asyncio
from mcp.server.fastmcp import FastMCP, Context
from playwright.async_api import async_playwright
from pyotp import TOTP
from playwright.async_api import async_playwright
import asyncio
import dotenv
import tracemalloc


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
    tracemalloc.start()
    url = "https://degreeworks.cuny.edu/Dashboard_lc"
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


            await page.wait_for_load_state('networkidle')

            await page.wait_for_selector("div[id='student-details']", timeout=timeout)
            # Extract fully rendered HTML
            #html = await page.content()
            html = await page.inner_html("main[id='main-content']")
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
    cuny_degree_mcp.run()
