import json
import os
import sys
import tracemalloc
from pathlib import Path
from typing import Literal, Any
from mcp.server.fastmcp import FastMCP, Context, Image
from mcp.types import TextContent
from playwright.async_api import async_playwright

from cuny_core_functions import get_cuny_information, get_cuny_id_card, get_course_details
from cuny_handles import handle_login_page, handle_otp_page, handle_criteria_page, handle_degreeworks_page, \
    handle_financial_page
from cuny_helper_functions import get_otp
from loguru import logger

logger.remove()
logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])

cuny_info_mcp = FastMCP("cuny-info-fetcher")

@cuny_info_mcp.tool(
    description="This is a server to fetch all cuny information such as financial tuition and cost, degree information and courses taking and current courses in progress. This function is an all in one function that should be used over the single functions as the single function takes too much time to fetch the information however this function is much quicker because it does everything all at once.",
    title="Fetch All Cuny Information",
    name="fetch_my_cuny_information"
)
async def fetch_my_cuny_information(
    ctx: Context,
    headless: bool = True,
) -> dict:
    """
    Fetches all information from CUNY, including data on financial tuition and cost, degree
    information, current and in-progress courses, and more. This function consolidates the
    execution of multiple individual operations, making it more time-efficient compared to
    using separate functions.

    :param ctx: The context required for executing the function.
    :type ctx: Context
    :param headless: Indicates whether the browser should operate in headless mode. Defaults to True.
    :type headless: bool
    :return: A dictionary containing the result of the operation. The dictionary includes the
        status (success or error), the CUNY URL, and either the serialized JSON data or an
        error message in case of a failure.
    :rtype: dict
    """
    tracemalloc.start()
    url = "http://cunyfirst.cuny.edu/"
    try:
        content = await get_cuny_information(url, headless=headless)
        jsonStr = json.dumps(content)
        return {
            "status": "success",
            "url": url,
            "json_length": len(jsonStr),
            "json": jsonStr
        }
    except Exception as e:
        return {
            "status": "error",
            "url": url,
            "error": str(e)
        }



@cuny_info_mcp.tool(
    description="A server that retrieves CUNY course schedules and details listed on your profile. Can be used to check times and dates of classes.",
    title="Fetch Cuny Courses",
    name="fetch_my_cuny_courses"
)
async def fetch_my_cuny_courses(
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

            if "portaldown.cuny.edu" in page.url:
                return {"status": "error", "url": url, "error": "Portal is down"}

            # Optional: wait for specific dynamic content to appear
            email, password, otp = get_otp()
            await ctx.info(f"Logging in as {email}")
            await handle_login_page(page)
            await ctx.log("info","Entering OTP...")
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
            courses_json = json.dumps(courses)

            return {
                "status": "success",
                "url": url,
                "json_length": len(courses_json),
                "json": courses_json
            }

        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
        finally:
            await browser.close()



@cuny_info_mcp.tool(
    description="A server that retrieves CUNY degree progress. It contains transcript, grades, and other academic information.",
    title="Fetch Cuny Degree Progress",
    name="fetch_my_cuny_degree_progress"
)
async def fetch_my_cuny_degree_progress(
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

            if "portaldown.cuny.edu" in page.url:
                return {"status": "error", "url": url, "error": "Portal is down"}

            # Optional: wait for specific dynamic content to appear
            email, password, otp = get_otp()
            await ctx.info(f"Logging in as {email}")
            await handle_login_page(page)
            await ctx.log("info","Entering OTP...")
            await handle_otp_page(page)

            degree_information_json = json.dumps(await handle_degreeworks_page(page))

            return {
                "status": "success",
                "url": url,
                "json_length": len(degree_information_json),
                "json": degree_information_json
            }

        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
        finally:
            await browser.close()


@cuny_info_mcp.tool(
    description="A server that retrieves the cost of CUNY course per semester. it checks how much money you will pay for each semester, or how much money you owe.",
    title="Fetch Cuny Financial Cost",
    name="fetch_my_cuny_financial_cost"
)
async def fetch_my_cuny_financial_cost(
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
            await handle_login_page(page)
            await ctx.log("info", "Entering OTP...")
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
            financial_cost_json = json.dumps(await handle_financial_page(page))

            return {
                "status": "success",
                "url": url,
                "json_length": len(financial_cost_json),
                "json": financial_cost_json
            }

        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
        finally:
            await browser.close()


@cuny_info_mcp.tool(
    description="This function is used to fetch the cuny student ID of the user.",
    title="Fetch All Cuny Student ID",
    name="fetch_my_cuny_student_id"
)
async def fetch_my_cuny_student_id(ctx: Context, type_of_card: Literal["getEmplidCard", "getLibraryIdCard", "both"] = "getEmplidCard"):
    """
    Fetches the CUNY Student ID for the user based on the specified type of card.

    The function communicates with an external system to retrieve the required
    CUNY Student ID. The specific type of card to fetch is controlled by the
    `typeOfCard` parameter. The function operates asynchronously and will notify
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
            if Path(os.getcwd() + f"/getEmplidCard.png").exists():
                response.append(Image(path=os.getcwd() + f"/getEmplidCard.png", format='png'))
            if Path(os.getcwd() + f"/getLibraryIdCard.png").exists():
                response.append(Image(path=os.getcwd() + f"/getLibraryIdCard.png", format='png'))
            if len(response) == 0:
                response.append(
                    TextContent(type="text", text=f"No card(s) found")
                )
            return response
        elif Path(os.getcwd() + f"/{type_of_card}.png").exists():
            return [Image(path=os.getcwd() + f"/{type_of_card}.png", format='png')]
        else:
            return [TextContent(type="text", text=f"No card(s) found")]

    await ctx.info("Fetching CUNY Student ID")
    result = get_image_path(type_of_card)
    if result[0] is not TextContent:
        return result
    await ctx.info(
        "CUNY Student ID not found in cache, fetching CUNY Student ID"
    )
    results = await get_cuny_id_card(headless=True, type_of_card=type_of_card)
    await ctx.info("CUNY Student ID fetched")
    return get_image_path(type_of_card)


@cuny_info_mcp.tool(
    description="This function is used to search for courses on CUNY. It takes a query string as input and returns a dictionary containing the search results. DO NOT ASSUME A COURSE NUMBER IF A COURSE NUMBER IF a-zA-Z text is being used",
    title="Search Courses on CUNY",
    name="search_courses_on_cuny"
)
async def search_courses_on_cuny(ctx: Context, query: str, college: Literal["leh01"] = "leh01"):
    return await get_course_details(query, college, ctx)


@cuny_info_mcp.tool(
    description="This function resolves the section code based on the provided year and semester.",
    title="Resolve Section Code",
    name="resolve_section_code"
)
async def resolve_section_code(year: int, semester: Literal["spring", "summer", "fall"] = "spring"):
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


if __name__ == "__main__":
    # Runs MCP server over stdio by default
    cuny_info_mcp.run()
