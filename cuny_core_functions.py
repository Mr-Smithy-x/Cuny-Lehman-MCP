import asyncio
import json
import tracemalloc

from mcp.server.fastmcp import Context
from playwright.async_api import async_playwright, Page
from typing_extensions import Literal

from cuny_handles import cuny_url_handles, handle_login_page, handle_otp_page, terms_list, term_courses, \
    financial_semester, degree_information, fetch_cuny_id
from cuny_helper_functions import get_current_term, next_term, parse_section_code, get_course_detail, search_courses
from meaning import shrink_search_response, shrink_get_course_detail


async def lehman360(page: Page):
    await page.goto("https://lehman360.lehman.edu")

    await handle_login_page(page)

    await handle_otp_page(page)

async def get_cuny_information(url: str, headless: bool = True):
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

        page.on("domcontentloaded", cuny_url_handles)
        await page.goto(url, wait_until="domcontentloaded")

        if "portaldown.cuny.edu" in page.url:
            return {"status": "error", "url": url, "error": "Portal is down"}

        await page.wait_for_url("**/psc/cnyihprd/EMPLOYEE/EMPL/c/**", wait_until="domcontentloaded")
        await asyncio.sleep(1)

        async with page.expect_popup() as popup_info:
            await page.click("div[id='win0groupletPTNUI_LAND_REC_GROUPLET$13']")

        new_page = await popup_info.value

        async with new_page.expect_event('close') as event_info:
            new_page.on("domcontentloaded", cuny_url_handles)

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

async def get_cuny_id_card(headless: bool = True, type_of_card: Literal["getEmplidCard", "getLibraryIdCard", "both"] = "getEmplidCard"):
    """
    Fetches a user's CUNY ID from the Lehman 360 portal.

    This function uses Playwright to interact with the Lehman 360 portal and retrieve the
    user's CUNY ID. It navigates through the login and OTP verification pages before
    fetching the desired card information based on the specified card type.

    :param headless: Determines whether the browser should run in headless mode.
    :type headless: bool
    :param type_of_card: The type of card to fetch. Must be one of "getEmplidCard" or
        "getLibraryIdCard". Defaults to "getEmplidCard". both will fetch both types of cards.
    :type type_of_card: Literal["getEmplidCard", "getLibraryIdCard", "both"]
    :return: The fetched CUNY ID based on the specified card type.
    :rtype: str
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await browser.new_page()
        await lehman360(page)
        return await fetch_cuny_id(page, type_of_card=type_of_card)

async def get_course_details(query: str, college: Literal["leh01"] = "leh01", ctx: Context = None):
    if ctx:
        await ctx.info("Searching courses")
    results = await search_courses(query=query, college=college)
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
    results_dict = await get_course_details("CMP 765", None)

        #print(json.dumps(result, indent=4))
    print(json.dumps(results_dict, indent=4))

    #print(f"Current OTP: {otp}")

#asyncio.run(main())