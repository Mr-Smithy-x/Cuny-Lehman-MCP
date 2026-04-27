import json

from mcp.server.fastmcp import Context
from pyotp import TOTP
from playwright.async_api import async_playwright, Page
import asyncio
import dotenv
import tracemalloc
import requests

from typing_extensions import Literal

from meaning import shrink_search_response, shrink_get_course_detail

def get_otp():
    """
    login url
    https://ssologin.cuny.edu/oam/server/obrareq.cgi

    otp url
    https://ssologin.cuny.edu/oaa-totp-factor/rui/index.html
    """
    loc = dotenv.find_dotenv('.env')
    env = dotenv.load_dotenv(loc)
    secret = str(dotenv.get_key(loc, "CUNY_TOPT"))
    email = str(dotenv.get_key(loc, "CUNY_EMAIL"))
    password = str(dotenv.get_key(loc, "CUNY_PASSWORD"))
    otp = TOTP(secret)
    toptime = otp.now()
    return (email, password, toptime)

terms_list = dict()
term_courses = dict()
financial_semester = dict()
degree_information = dict()

async def handle_login_page(page: Page):
    """
    Handles the login page by filling in credentials and submitting the form.

    :param page: The Playwright Page object representing the browser page.
    :type page: Page
    :return: None
    """
    print("Login page loaded", page.url)
    await page.wait_for_selector("input[name=usernameDisplay]", timeout=15000)
    email, password, otp = get_otp()
    await page.fill("input[name=usernameDisplay]", email)
    await page.fill("input[name=password]", password)
    await page.click("button[type=submit]")

async def handle_otp_page(page: Page):
    """
    Handles the OTP authentication page by entering the OTP and submitting.

    :param page: The Playwright Page object representing the browser page.
    :type page: Page
    :return: None
    """
    await page.wait_for_selector("input[placeholder='Enter TOTP']", timeout=15000)
    print("OTP page loaded", page.url)
    email, password, otp = get_otp()
    await page.fill("input[placeholder='Enter TOTP']", otp)
    await page.wait_for_selector("button[class=oj-button-button]")
    await page.click("button[class=oj-button-button]")

async def handle_criteria_page(page: Page):
    """
    Handles the criteria page by extracting terms and courses information.

    :param page: The Playwright Page object representing the browser page.
    :type page: Page
    :return: None
    """
    print("Criteria page loaded", page.url)
    await page.wait_for_selector("div[id='welcomeTerms']", timeout=30000)
    page_content = await page.query_selector_all("div[id='welcomeTerms'] div[data-term]")
    for term in page_content:
        title = (await (await term.query_selector("a.term-card-title")).inner_text())
        detail = (await (await term.query_selector("div.term-card-detail")).inner_text())
        link = await term.get_attribute("data-term")
        terms_list[title] = (link, detail)

    await page.evaluate("this.window.UU.caseToggleLegend()")
    for index, (semester, (link, detail)) in enumerate(terms_list.items()):
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
    return {'terms': terms_list, 'courses': term_courses}

async def handle_degreeworks_page(page: Page):
    """
    Handles the degreeworks page by extracting degree information.

    :param page: The Playwright Page object representing the browser page.
    :type page: Page
    :return: None
    """
    await page.wait_for_load_state('networkidle', timeout=10000)
    await page.wait_for_selector("div[id='student-details']", timeout=15000)
    # Extract fully rendered HTML
    # html = await page.content()
    # html = await page.inner_html("main[id='main-content']")
    degree = await page.inner_text("main[id='main-content']")
    degree_information["content"] = degree
    print(degree)
    try:
        await page.close()
    except:
        pass
    return degree_information

async def handle_financial_page(page: Page):
    """
    Handles the financial account page by extracting semester costs information.

    :param page: The Playwright Page object representing the browser page.
    :type page: Page
    :return: None
    """
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
    return financial_semester

async def handle_other_pages(page: Page):
    """
    Handles all other pages that don't match the specific URL patterns.

    :param page: The Playwright Page object representing the browser page.
    :type page: Page
    :return: None
    """
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

async def lehman360(page: Page):
    await page.goto("https://lehman360.lehman.edu")

    await handle_login_page(page)

    await handle_otp_page(page)

    await fetch_cuny_id(page)

async def fetch_cuny_id(page: Page, typeOfCard: Literal["getEmplidCard", "getLibraryIdCard", "both"] = "getEmplidCard") -> bytes:
    """
    Fetches a screenshot of a specific CUNY ID card type by interacting with a web page. The function waits for a
    specific card type button to appear on the page, clicks it, waits for the content to load, and then captures
    a screenshot of the resulting dialog content.

    :param page: The Playwright Page object to interact with the web page.
    :type page: Page
    :param typeOfCard: Specifies the type of CUNY ID card to fetch. Should be either "getEmplidCard" or "getLibraryIdCard".
                       Defaults to "getEmplidCard". If set to "both", both types of cards will be fetched in one call.
                       No need to call the function twice.
    :type typeOfCard: Literal["getEmplidCard", "getLibraryIdCard", "both"]
    :return: A screenshot of the CUNY ID card content as bytes.
    :rtype: bytes
    """
    if typeOfCard == "both":
        await page.wait_for_selector("#getEmplidCard")
        await page.click("#getEmplidCard")
        await asyncio.sleep(2)
        await page.locator("div[id='swal2-content']").screenshot(path=f"getEmplidCard.png")
        await asyncio.sleep(1)
        await page.click("button.swal2-close")
        await page.wait_for_selector("#getLibraryIdCard")
        await page.click("#getLibraryIdCard")
        await asyncio.sleep(2)
        return await page.locator("div[id='swal2-content']").screenshot(path=f"getLibraryIdCard.png")
    else:
        await page.wait_for_selector(f"#{typeOfCard}")
        await page.click(f"#{typeOfCard}")
        await asyncio.sleep(2)
        return await page.locator("div[id='swal2-content']").screenshot(path=f"{typeOfCard}.png")

async def function(page: Page):
    """
    Handles navigation and interaction with specific web pages in an asynchronous manner
    using the Playwright Page object. Supports custom actions based on the current page's
    URL, including login, OTP authentication, navigating terms and courses, querying
    degree information, and retrieving financial data.

    :param page: The Playwright Page object representing the browser page where the
                 interactions will occur.
    :type page: Page

    :raises ValueError: Raises an exception if any required page element is absent or
                        an unforeseen page URL is encountered.

    :return: None
    """
    if "https://ssologin.cuny.edu/oam/server/obrareq.cgi" in page.url:
        await handle_login_page(page)
    elif "https://ssologin.cuny.edu/oaa-totp-factor/rui/index.html" in page.url:
        await handle_otp_page(page)
    elif "https://sb.cunyfirst.cuny.edu/criteria.jsp" in page.url:
        await handle_criteria_page(page)
    elif "https://degreeworks.cuny.edu/Dashboard_lc" in page.url:
        await handle_degreeworks_page(page)
    elif "https://cssa.cunyfirst.cuny.edu/psc/cnycsprd_6/EMPLOYEE/SA/c/SSF_STUDENT_FL.SSF_FIN_ACCT_MD_FL.GBL" in page.url:
        await handle_financial_page(page)
    else:
        await handle_other_pages(page)

async def cuny_browser_login(url: str, headless: bool = True):
    """
    Performs automated login to the CUNY browser system using Playwright and navigates through
    several system pages to extract information such as terms, courses, tuition details, and
    degree information.

    :param url: URL to the login page of the CUNY system.
    :type url: str
    :param headless: Indicates whether the browser should run in headless mode. Defaults to True.
    :type headless: bool
    :return: A dictionary containing extracted data including terms, courses, tuition details,
        and degree information.
    :rtype: dict
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)

        context = await browser.new_context()
        page = await browser.new_page()

        page.on("domcontentloaded", function)
        await page.goto(url, wait_until="domcontentloaded")

        if "portaldown.cuny.edu" in page.url:
            return {"status": "error", "url": url, "error": "Portal is down"}

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

async def l360(headless: bool = True, typeOfCard: Literal["getEmplidCard", "getLibraryIdCard", "both"] = "getEmplidCard"):
    """
    Fetches a user's CUNY ID from the Lehman 360 portal.

    This function uses Playwright to interact with the Lehman 360 portal and retrieve the
    user's CUNY ID. It navigates through the login and OTP verification pages before
    fetching the desired card information based on the specified card type.

    :param headless: Determines whether the browser should run in headless mode.
    :type headless: bool
    :param typeOfCard: The type of card to fetch. Must be one of "getEmplidCard" or
        "getLibraryIdCard". Defaults to "getEmplidCard".
    :type typeOfCard: Literal["getEmplidCard", "getLibraryIdCard"]
    :return: The fetched CUNY ID based on the specified card type.
    :rtype: str
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)

        context = await browser.new_context()
        page = await browser.new_page()
        await page.goto("https://lehman360.lehman.edu", wait_until="networkidle")
        await handle_login_page(page)
        await handle_otp_page(page)
        return await fetch_cuny_id(page, typeOfCard=typeOfCard)

def get_current_term(college: Literal["leh01"] = "leh01"):

    url = f"https://app.coursedog.com/api/v1/{college}/general/currentTerm"

    payload = {}
    headers = {
        'Pragma': 'no-cache',
        'Accept': 'application/json, text/plain, */*',
        'Sec-Fetch-Site': 'cross-site',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Sec-Fetch-Mode': 'cors',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Origin': 'https://lehman-graduate.catalog.cuny.edu',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.4 Safari/605.1.15',
        'Referer': 'https://lehman-graduate.catalog.cuny.edu/',
        'Sec-Fetch-Dest': 'empty',
        'X-Requested-With': 'catalog',
        'Priority': 'u=3, i'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()

def next_term(term: str = str(get_current_term()['id']), academic_year: bool = False):
    year = int(term[1:3])
    if term[-1] == "2":
        if academic_year:
            term = term[:-1] + "9"
        else:
            term = term[:-1] + "6"
    elif term[-1] == "6":
        term = term[:-1] + "9"
    elif term[-1] == "9":
        term = term[:-3] + str(year + 1) + "2"
    else:
        return "Error: Invalid term"
    return term

def resolve_section_code(year: int, semester: Literal["spring", "summer", "fall"] = "spring"):
    """
    This function resolves the section code based on the provided year and semester.
    The section code is constructed using the century bit (to distinguish between
    centuries), the last two digits of the year, and a code representing the semester.

    For example:
    Given a section code 1262, 1266, 1269 determines what year and semester it is in.
    - 1262 is the first semester (spring),
    - 1266 is the second semester (summer),
    - 1269 is the third semester (summer).
    How does this work? take the format: (century_bit)[year_abbreviated]<month> to be (1)[26]<2>
    - (1) - signifies that we are in years of 2000s while (0) signifies we are below 1999 and below
    - [26] - signifies we are in 2026
    - <2> - signifies what month the semester starts

    :param year: The four-digit year for which the section code is being resolved.
    :type year: int
    :param semester: The semester for which the section code is being resolved.
        Must be one of "spring", "summer", or "fall". Defaults to "spring".
    :type semester: Literal["spring", "summer", "fall"]
    :return: The resolved section code as an integer, composed of the century bit,
        the last two digits of the year, and the month code for the semester.
    :rtype: int
    """
    # Determine century bit: 1 for 2000+, 0 for 1999 and below
    century_bit = 1 if year >= 2000 else 0

    # Extract two-digit year abbreviation
    year_abbreviated = year % 100

    # Map semester to month code
    semester_month_map = {
        "spring": 2,
        "summer": 6,
        "fall": 9
    }

    month_code = semester_month_map[semester]

    # Combine to form section code: century_bit + year_abbreviated + month_code
    section_code = int(f"{century_bit}{year_abbreviated}{month_code}")

    return section_code

def parse_section_code(section_code: str) -> tuple[int, Literal["spring", "summer", "fall"]]:
    """
    This function parses a section code to extract the year and semester.
    The section code is composed of a century bit, two-digit year abbreviation,
    and a month code representing the semester.

    For example:
    Given a section code 1262, 1266, 1269:
    - 1262 represents spring 2026
    - 1266 represents summer 2026
    - 1269 represents fall 2026

    The format is: (century_bit)[year_abbreviated]<month>
    - (1) - signifies years 2000 and above; (0) signifies 1999 and below
    - [26] - signifies year 2026
    - <2> - signifies the semester (2=spring, 6=summer, 9=fall)

    :param section_code: The section code to parse, composed of century bit,
        year abbreviation, and month code.
    :type section_code: int
    :return: A tuple containing the four-digit year and the semester name.
    :rtype: tuple[int, Literal["spring", "summer", "fall"]]
    :raises ValueError: If the section code format is invalid or month code is unrecognized.
    """
    # Convert to string for easier parsing
    code_str = str(section_code)

    if len(code_str) != 4:
        raise ValueError(f"Invalid section code format: {section_code}. Expected 4 digits.")

    # Extract components
    century_bit = int(code_str[0])
    year_abbreviated = int(code_str[1:3])
    month_code = int(code_str[3])

    # Determine full year based on century bit
    if century_bit == 1:
        year = 2000 + year_abbreviated
    elif century_bit == 0:
        year = 1900 + year_abbreviated
    else:
        raise ValueError(f"Invalid century bit: {century_bit}. Expected 0 or 1.")

    # Map month code to semester
    month_semester_map = {
        2: "spring",
        6: "summer",
        9: "fall"
    }

    semester = month_semester_map.get(month_code)
    if semester is None:
        raise ValueError(f"Invalid month code: {month_code}. Expected 2, 6, or 9.")

    return (year, semester)

def get_course_detail(id: str, sisId: str, rawCourseId: str, section: str, college: Literal["leh01"] = "leh01"):
    if len(section) != 4:
        raise ValueError("code must be exactly 4 characters long")

    if not section.isnumeric():
        raise ValueError("code must be numeric")

    url = f"https://app.coursedog.com/api/v1/ca/{college}/sections/{section}/{sisId}?includeRelatedData=true&courseIds={id},{rawCourseId}"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()

async def get_active_catalog(page: Page):
    await page.goto("https://lehman-graduate.catalog.cuny.edu/courses", wait_until="domcontentloaded")
    activeCatalog = await page.evaluate("this.__NUXT__.state.settings.activeCatalog")
    return activeCatalog

def search(query: str, catalog: str, college: Literal["leh01"] = "leh01"):

    url = f"https://app.coursedog.com/api/v1/cm/{college}/courses/search/{query}?catalogId={catalog}&skip=0&limit=20"

    payload = json.dumps({
        "condition": "AND",
        "filters": [
            {
                "condition": "and",
                "filters": [
                    {
                        "id": "status-course",
                        "name": "status",
                        "inputType": "select",
                        "group": "course",
                        "type": "is",
                        "value": "Active"
                    },
                    {
                        "id": "catalogPrint-course",
                        "name": "catalogPrint",
                        "inputType": "boolean",
                        "group": "course",
                        "type": "is",
                        "value": True
                    },
                    {
                        "id": "career-course",
                        "name": "career",
                        "inputType": "careerSelect",
                        "group": "course",
                        "type": "isNot",
                        "value": "Undergraduate"
                    }
                ]
            }
        ]
    })
    headers = {
        'Content-Type': 'application/json',
        'Pragma': 'no-cache',
        'Accept': 'application/json, text/plain, */*',
        'Sec-Fetch-Site': 'cross-site',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Sec-Fetch-Mode': 'cors',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Origin': 'https://lehman-graduate.catalog.cuny.edu',
        'Content-Length': '406',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.4 Safari/605.1.15',
        'Referer': 'https://lehman-graduate.catalog.cuny.edu/',
        'Sec-Fetch-Dest': 'empty',
        'X-Requested-With': 'catalog',
        'Priority': 'u=3, i'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    return response.json()

async def search_courses(query: str):

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        catalog = await get_active_catalog(page)
        result = search(query, catalog)
        return result


async def query_courses(query: str, college: Literal["leh01"] = "leh01", ctx: Context = None):
    if ctx:
        await ctx.info("Searching courses")
    results = await search_courses(query=query)
    if ctx:
        await ctx.info(f"Found {len(results)} courses for query '{query}'")
    shrunk = shrink_search_response(results)
    if ctx:
        await ctx.info(f"Shrunk search response to {len(shrunk)} courses")
    results_dict = dict()

    currentTerm = get_current_term()['id']
    if ctx:
        await ctx.info(f"Current term: {currentTerm}")

    nextTerm = next_term(term=str(currentTerm), academic_year=True)
    if ctx:
        await ctx.info(f"Next term: {nextTerm}")
    parsed_currentTerm = parse_section_code(currentTerm)
    if ctx:
        await ctx.info(f"Parsed current term: {parsed_currentTerm}")
    parsed_nextTerm = parse_section_code(nextTerm)
    if ctx:
        await ctx.info(f"Parsed next term: {parsed_nextTerm}")

    for course in shrunk:
        if ctx:
            await ctx.info(f"Processing course: {course['name']}")
        currentTermResults = get_course_detail(course['id'], course['sisId'], course['rawCourseId'], currentTerm)
        if ctx:
            await ctx.info(f"Got course detail for {course['name']}")
        nextTermResults = get_course_detail(course['id'], course['sisId'], course['rawCourseId'], nextTerm)
        if ctx:
            await ctx.info(f"Got course detail for {course['name']} in next term")
        results_dict[course['name']] = {
            f"{parsed_currentTerm[1] + str(parsed_currentTerm[0])}": shrink_get_course_detail(currentTermResults),
            f"{parsed_nextTerm[1] + str(parsed_nextTerm[0])}": shrink_get_course_detail(nextTermResults),
        }
    results['searches'] = shrunk

    if ctx:
        await ctx.info(f"Completed processing {len(shrunk)} courses")
    return {
        "status": "success",
        "query": query,
        "results": results_dict,
        "current_term": parsed_currentTerm[1] + str(parsed_currentTerm[0]),
        "next_term": parsed_nextTerm[1] + str(parsed_nextTerm[0]),
        "$hint": "use the fields current_term and next_term to distinguish between the results. "
                 "It is obvious that current_term refers to the current term and next_term refers to "
                 "the next term and you may not be able to register for courses in the current term. "
                 "if there are course materials please display them, you may also check textBook field, "
                 "credit hours are important to know as well as when the class with start and end also the time and days. "
                 "if descriptions of the course are present display the description of the course and notes."
    }

async def main():
    tracemalloc.start()
    login_url = "http://cunyfirst.cuny.edu/"
    #await login(login_url, wait_for_selector="input[name=usernameDisplay]")
    #results = await cuny_browser_login(login_url, headless=False)
    #results = await l360(headless=False, typeOfCard="both")
    print(next_term(term="1269",academic_year=False))
    #results_dict = await query_courses("Artificial Intelligence")
    results_dict = await query_courses("CMP 765", None)

        #print(json.dumps(result, indent=4))
    print(json.dumps(results_dict, indent=4))

    #print(f"Current OTP: {otp}")

#asyncio.run(main())