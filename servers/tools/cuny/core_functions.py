import tracemalloc
from pathlib import Path

from loguru import logger
from mcp.server.fastmcp import Context, Image
from mcp.types import TextContent
from typing_extensions import Any

from .handles import *
from .helper_functions import *
from .response_reducer import *


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
            await page.click("div[groupletid=CU_SCHEDULE_BUILDER]")

        new_page = await popup_info.value

        async with new_page.expect_event('close') as event_info:
            new_page.on("domcontentloaded", cuny_url_handles)

        response = await event_info.value
        logger.info("Event processing complete.")

        await page.click("div[groupletid=CS_SSF_FIN_ACCT_ML_FL_GB_LNK]")
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        await page.goto("https://degreeworks.cuny.edu/Dashboard_lc", wait_until="domcontentloaded")
        await asyncio.sleep(1)

        async with page.expect_event('close') as event_info:
            print("Waiting to close...")

        response = await event_info.value
        logger.info("Event processing complete.")
        await context.close()
        await browser.close()
        return { "terms": terms_list, "courses": term_courses, "tuition": financial_semester, "degree_information": degree_information}

async def get_cuny_id_card(headless: bool = True,
                           type_of_card: Literal["getEmplidCard", "getLibraryIdCard", "both"] = "getEmplidCard") -> \
list[bytes]:
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

async def get_course_details(query: str, college: Literal["leh01"] = "leh01"):
    logger.info("Searching courses")
    results = await search_courses(query=query, college=college)
    logger.info(f"Found {len(results)} courses for query '{query}'")
    shrunk = reduce_search_response(results)
    logger.info(f"Shrunk search response to {len(shrunk)} courses")
    results_dict = dict()

    currentTerm = get_current_term()['id']
    logger.info(f"Current term: {currentTerm}")

    nextTerm = next_term(term=str(currentTerm), academic_year=True)
    logger.info(f"Next term: {nextTerm}")
    parsed_currentTerm = parse_section_code(currentTerm)
    logger.info(f"Parsed current term: {parsed_currentTerm}")
    parsed_nextTerm = parse_section_code(nextTerm)
    logger.info(f"Parsed next term: {parsed_nextTerm}")

    for course in shrunk:
        logger.info(f"Processing course: {course['name']}")
        currentTermResults = get_course_detail(course['id'], course['sisId'], course['rawCourseId'], currentTerm)
        logger.info(f"Got course detail for {course['name']}")
        nextTermResults = get_course_detail(course['id'], course['sisId'], course['rawCourseId'], nextTerm)
        logger.info(f"Got course detail for {course['name']} in next term")
        results_dict[course['name']] = {
            f"{parsed_currentTerm[1] + str(parsed_currentTerm[0])}": reduce_course_detail_response(currentTermResults),
            f"{parsed_nextTerm[1] + str(parsed_nextTerm[0])}": reduce_course_detail_response(nextTermResults),
        }
    results['searches'] = shrunk

    logger.info(f"Completed processing {len(shrunk)} courses")
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


async def get_my_cuny_student_id(type_of_card: Literal["getEmplidCard", "getLibraryIdCard", "both"] = "getEmplidCard", ctx: Context = None):
    """
    Fetches the CUNY Student ID for the user based on the specified type of card.

    The function communicates with an external system to retrieve the required
    CUNY Student ID. The specific type of card to fetch is controlled by the
    `type_of_card` parameter. The function operates asynchronously and will notify
    the user through the context object when the operation begins and completes.

    :param ctx: The context object used for providing information updates during
        the execution of the function.
    :type ctx: Context
    :param type_of_card: The type of card for which the CUNY Student ID should be
        fetched. Valid options are "getEmplidCard" or "getLibraryIdCard" or "both". Defaults
        to "getEmplidCard". If set to both, both types of cards will be fetched in one call
        no need to call the function twice.
    :return: A list containing an image with the path to the fetched card image
        and its format.
    :rtype: list[Image]
    """
    def get_image_path(image_name: str) -> list[Any] | list[Image] | list[TextContent]:
        if type_of_card == "both":
            response = []
            if Path(f"getEmplidCard.png").exists():
                response.append(Image(path=f"getEmplidCard.png", format='png'))
            if Path(f"getLibraryIdCard.png").exists():
                response.append(Image(path=f"getLibraryIdCard.png", format='png'))
            if len(response) == 0:
                response.append(
                    TextContent(type="text", text=f"No card(s) found")
                )
            return response
        elif Path(f"{image_name}.png").exists():
            return [Image(path=f"{image_name}.png", format='png')]
        else:
            return [TextContent(type="text", text=f"No card(s) found")]

    logger.info("Fetching CUNY Student ID")

    result = get_image_path(type_of_card)

    if not isinstance(result[0], TextContent):
        print(result)
        return result

    logger.info("CUNY Student ID not found in cache, fetching CUNY Student ID")

    results = await get_cuny_id_card(headless=True, type_of_card=type_of_card)
    logger.info("CUNY Student ID fetched")
    return get_image_path(type_of_card)

async def main():
    tracemalloc.start()
    login_url = "http://cunyfirst.cuny.edu/"
    #await login(login_url, wait_for_selector="input[name=usernameDisplay]")
    #results = await cuny_browser_login(login_url, headless=False)
    #results = await l360(headless=False, typeOfCard="both")
    print(next_term(term="1269", academic_year=False))
    #results_dict = await query_courses("Artificial Intelligence")
    results_dict = await get_course_details("CMP 765", None)

        #print(json.dumps(result, indent=4))
    print(json.dumps(results_dict, indent=4))

    #print(f"Current OTP: {otp}")

#asyncio.run(main())