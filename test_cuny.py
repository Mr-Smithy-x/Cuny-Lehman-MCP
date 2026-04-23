import json

from pyotp import TOTP
from playwright.async_api import async_playwright, Page
import asyncio
import dotenv
import tracemalloc

"""
login url
https://ssologin.cuny.edu/oam/server/obrareq.cgi

otp url
https://ssologin.cuny.edu/oaa-totp-factor/rui/index.html

"""
terms_list = dict()
term_courses = dict()
financial_semester = dict()
degree_information = dict()

async def function(page: Page):
    if "https://ssologin.cuny.edu/oam/server/obrareq.cgi" in page.url:
        print("Login page loaded", page.url)
        email, password, otp = get_otp()
        await page.fill("input[name=usernameDisplay]", email)
        await page.fill("input[name=password]", password)
        await page.click("button[type=submit]")
    elif "https://ssologin.cuny.edu/oaa-totp-factor/rui/index.html" in page.url:
        print("OTP page loaded", page.url)
        email, password, otp = get_otp()
        await page.fill("input[placeholder='Enter TOTP']", otp)
        await page.wait_for_selector("button[class=oj-button-button]")
        await page.click("button[class=oj-button-button]")
    elif "https://sb.cunyfirst.cuny.edu/criteria.jsp" in page.url:
        print("Criteria page loaded", page.url)
        await page.wait_for_selector("div[id='welcomeTerms']", timeout=30000)
        page_content = await page.query_selector_all("div[id='welcomeTerms'] div[data-term]")
        for term in page_content:
            title = (await (await term.query_selector("a.term-card-title")).inner_text())
            detail = (await (await term.query_selector("div.term-card-detail")).inner_text())
            link = await term.get_attribute("data-term")
            terms_list[title] = (link, detail)

        await page.evaluate("this.window.UU.caseToggleLegend()")
        for index, (semester, (link, detail))  in enumerate(terms_list.items()):
            try:
                print(f"Getting courses for {semester}")
                evaluate_result = await page.evaluate(f"this.window.UU.caseTermContinue({link});")
                await page.wait_for_selector("div[id=legend_box]", timeout=10000)
                await asyncio.sleep(2)
                html_courses = await page.query_selector_all('div[id=legend_box] div.legend_table')
                courses = []
                for course in html_courses:
                    text = await course.inner_text()
                    courses.append(text)
                term_courses[semester] = courses
                await page.go_back()
                await asyncio.sleep(1)
                print(f"Index {index}, Semester: {semester}, {courses}\n")
            except:
                try:
                    await page.go_back()
                except:
                    pass
                await asyncio.sleep(1)
                print(f"Error getting courses for {semester}")
        try:
            await page.close()
        except:
            pass
    elif "https://degreeworks.cuny.edu/Dashboard_lc" in page.url:
        await page.wait_for_load_state('networkidle', timeout=5000)
        await page.wait_for_selector("div[id='student-details']", timeout=15000)
        # Extract fully rendered HTML
        # html = await page.content()
        #html = await page.inner_html("main[id='main-content']")
        degree = await page.inner_text("main[id='main-content']")
        degree_information["content"] = degree
        print(degree)
        await page.close()
    elif "https://cssa.cunyfirst.cuny.edu/psc/cnycsprd_6/EMPLOYEE/SA/c/SSF_STUDENT_FL.SSF_FIN_ACCT_MD_FL.GBL" in page.url:
        await page.wait_for_selector("tbody.ps_grid-body tr.ps_grid-row.psc_rowact.psc_disabled")
        html_semester_costs = await page.query_selector_all("tbody.ps_grid-body tr.ps_grid-row.psc_rowact.psc_disabled")
        for semester in html_semester_costs:
            cells = await semester.query_selector_all("td")
            term = await cells[0].inner_text()
            charges = await cells[1].inner_text()
            pending_aid = await cells[2].inner_text()
            total_due = await cells[3].inner_text()
            financial_semester[term] = {"term": term, "charges": charges, "pending_aid": pending_aid,
                                        "total_due": total_due}
        print(financial_semester)
    else:
        if "https://ssologin.cuny.edu/oam/server/auth_cred_submit" in page.url:
            pass
        elif "https://ssologin.cuny.edu/oaa/authnui/index.html" in page.url:
            pass
        elif "/psc/cnyihprd/EMPLOYEE/EMPL/c/NUI_FRAMEWORK.PT_LANDINGPAGE.GBL?LP=CU_CS_SCC_STUDENT_HOMEPAGE_FL" in page.url:
            print("Student Center page loaded", page.url)
        elif "/psc/cnyihprd/EMPLOYEE/EMPL/c/NUI_FRAMEWORK.PT_LANDINGPAGE.GBL" in page.url:
            print("Main Dashboard page loaded", page.url)
            await page.goto(page.url[:-2] + "?LP=CU_CS_SCC_STUDENT_HOMEPAGE_FL", wait_until="domcontentloaded")
        else:
            print("Page is loaded: url = ", page.url, " title = ", page.title, "")

async def cuny_browser_login(url: str, headless: bool = True):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)

        context = await browser.new_context()
        page = await browser.new_page()

        page.on("domcontentloaded", function)
        await page.goto(url, wait_until="domcontentloaded")

        await page.wait_for_url("**/psc/cnyihprd/EMPLOYEE/EMPL/c/**", wait_until="domcontentloaded")
        await asyncio.sleep(1)

        async with page.expect_popup() as popup_info:
            await page.click("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$13']")

        new_page = await popup_info.value

        async with new_page.expect_event('close') as event_info:
            new_page.on("domcontentloaded", function)

        response = await event_info.value
        print("Event processing complete.")

        await page.click("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$16']")
        await asyncio.sleep(3)
        await page.goto("https://degreeworks.cuny.edu/Dashboard_lc", wait_until="domcontentloaded")
        await asyncio.sleep(1)

        async with page.expect_event('close') as event_info:
            print("Waiting to close...")

        response = await event_info.value
        print("Event processing complete.")
        await context.close()
        await browser.close()
        return { "terms": terms_list,"courses": term_courses,"tuition": financial_semester, "degree_information": degree_information }


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
    #await login(login_url, wait_for_selector="input[name=usernameDisplay]")
    results = await cuny_browser_login(login_url, headless=False)
    print(json.dumps(results))

    #print(f"Current OTP: {otp}")

#asyncio.run(main())