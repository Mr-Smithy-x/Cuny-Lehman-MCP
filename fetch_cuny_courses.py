import json
import tracemalloc

import dotenv
from mcp.server.fastmcp import FastMCP, Context
from playwright.async_api import async_playwright
from pyotp import TOTP

from test_cuny import handle_login_page, handle_otp_page, handle_criteria_page, term_courses

cuny_mcp = FastMCP("cuny-courses-fetcher")


def get_otp():
    loc = dotenv.find_dotenv('.env')
    env = dotenv.load_dotenv(loc)
    secret = str(dotenv.get_key(loc, "CUNY_TOPT"))
    email = str(dotenv.get_key(loc, "CUNY_EMAIL"))
    password = str(dotenv.get_key(loc, "CUNY_PASSWORD"))
    otp = TOTP(secret)
    toptime = otp.now()
    return email, password, toptime


@cuny_mcp.tool(
    description="A server that retrieves CUNY course schedules and details listed on your profile. Can be used to check times and dates of classes.",
    title="Fetch Cuny Courses",
    name="fetch_cuny_courses"
)
async def fetch_cuny_course(
    ctx: Context,
    timeout: int = 30000,
) -> dict:
    """
    A coroutine that fetches CUNY course schedules and details from the CUNY First platform.

    This function utilizes Playwright for browser automation and performs tasks such as
    login, OTP entry, navigation to the course details section, and extraction of rendered
    HTML content. The resulting information, including the status, URL, and extracted
    HTML data, is returned as a dictionary.

    :param ctx: The asynchronous context object used for logging and other utility methods.
    :type ctx: Context
    :param timeout: The maximum time, in milliseconds, to wait for page actions like navigation,
        element rendering, or dynamic content to load. Defaults to 30000 milliseconds.
    :type timeout: int
    :return: A dictionary containing the result of the operation. On success, it includes the
        status as "success," the source URL, and rendered HTML information such as length and
        content. On error, it returns the status as "error," the source URL, and the error message.
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

            # Optional: wait for specific dynamic content to appear
            email, password, otp = get_otp()
            await ctx.info(f"Logging in as {email}")
            await page.wait_for_selector("input[name=usernameDisplay]", timeout=timeout)

            await handle_login_page(page)
            await ctx.log("info","Entering OTP...")
            await page.wait_for_selector('input[placeholder="Enter TOTP"].oj-inputtext-input.oj-text-field-input.oj-component-initnode', timeout=timeout)

            await handle_otp_page(page)

            #student center
            await page.wait_for_selector("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$1']", timeout=timeout)
            await page.click("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$1']")

            #schedule builder
            await page.wait_for_selector("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$13']", timeout=timeout)

            await ctx.log("info","Going to schedule builder")

            async with page.expect_popup() as popup_info:
                await page.click("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$13']")

            await ctx.info("Waiting for popup...")
            new_page = await popup_info.value
            await ctx.info("Popup opened!")


            await new_page.wait_for_load_state('networkidle')
            await ctx.info(await new_page.title())

            courses = await handle_criteria_page(new_page)

            html = json.dumps(courses)

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
    cuny_mcp.run()
