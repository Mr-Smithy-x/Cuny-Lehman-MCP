from pyotp import TOTP
from playwright.async_api import async_playwright
import asyncio
import dotenv
import tracemalloc


def get_otp():
    loc = dotenv.find_dotenv('.env')
    env = dotenv.load_dotenv(loc)
    secret = str(dotenv.get_key(loc, "CUNY_TOPT"))
    email = str(dotenv.get_key(loc, "CUNY_EMAIL"))
    password = str(dotenv.get_key(loc, "CUNY_PASSWORD"))
    otp = TOTP(secret)
    toptime = otp.now()
    return (email, password, toptime)

async def login(
        url: str,
        wait_for_selector: str | None = None,
        timeout: int = 30000
) -> dict:
    """
    Fetch fully JavaScript-rendered HTML from a URL.
    Returns a dict with status, html, and metadata for better AI parsing.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await browser.new_page()

        try:
            # Navigate and wait for JS/network to settle
            await page.goto(url, wait_until="networkidle", timeout=timeout)

            # Optional: wait for specific dynamic content to appear
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=timeout)

            email, password, otp = get_otp()

            await page.fill("input[name=usernameDisplay]", email)
            await page.fill("input[name=password]", password)
            await page.click("button[type=submit]")


            await page.wait_for_selector('input[placeholder="Enter TOTP"].oj-inputtext-input.oj-text-field-input.oj-component-initnode', timeout=timeout)

            email, password, otp = get_otp()
            await page.fill('input[placeholder="Enter TOTP"].oj-inputtext-input.oj-text-field-input.oj-component-initnode', otp)
            await page.wait_for_selector("button[class=oj-button-button]", timeout=timeout)
            await page.click("button[class=oj-button-button]")

            #student center
            await page.wait_for_selector("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$1']", timeout=timeout)
            await page.click("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$1']")

            #schedule builder
            await page.wait_for_selector("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$13']", timeout=timeout)

            #new_page_future = context.wait_for_event("page")
            async with page.expect_popup() as popup_info:
                await page.click("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$13']")

            print("Waiting for popup...")
            new_page = await popup_info.value
            print("Popup opened!")


            await new_page.wait_for_load_state('networkidle')

            print(await new_page.title())
            await new_page.evaluate("() => this.window.UU.caseTermContinue(3202630);")
            await asyncio.sleep(1)
            #await new_page.evaluate("() => this.window.AS.openCourseBrowser();")

            #html = await page.inner_html('#legend_box')
            html = await new_page.inner_html('div[id="requirements"]')

            # Extract fully rendered HTML
            #html = await page.content()
            screenshot = await page.screenshot(path="screenshot.png")

            print(html)

            return {
                "status": "success",
                "url": url,
                "html_length": len(html),
                "html": html
            }

        except Exception as e:
            print(e)
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
        finally:
            await browser.close()


async def main():
    tracemalloc.start()
    login_url = "http://cunyfirst.cuny.edu/"
    await login(login_url, wait_for_selector="input[name=usernameDisplay]")
    print("Logged in")

    #print(f"Current OTP: {otp}")

asyncio.run(main())