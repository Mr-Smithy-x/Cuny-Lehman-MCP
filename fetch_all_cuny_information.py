import json
import os
import tracemalloc
from pathlib import Path
from typing import Literal, Any
from mcp.server.fastmcp import FastMCP, Context, Image
from mcp.types import TextContent
from cuny_core_functions import cuny_browser_login, l360, query_courses

cuny_info_mcp = FastMCP("cuny-info-fetcher")

@cuny_info_mcp.tool(
    description="This is a server to fetch all cuny information such as financial tuition and cost, degree information and courses taking and current courses in progress. This function is an all in one function that should be used over the single functions as the single function takes too much time to fetch the information however this function is much quicker because it does everything all at once.",
    title="Fetch All Cuny Information",
    name="fetch_cuny_information"
)
async def fetch_cuny_information(
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
        content = await cuny_browser_login(url, headless=headless)
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
    description="This function is used to fetch the cuny student ID of the user.",
    title="Fetch All Cuny Student ID",
    name="fetch_cuny_studentid"
)
async def fetch_cuny_studentid(ctx: Context, typeOfCard: Literal["getEmplidCard", "getLibraryIdCard", "both"] = "getEmplidCard"):
    """
    Fetches the CUNY Student ID for the user based on the specified type of card.

    The function communicates with an external system to retrieve the required
    CUNY Student ID. The specific type of card to fetch is controlled by the
    `typeOfCard` parameter. The function operates asynchronously and will notify
    the user through the context object when the operation begins and completes.

    :param ctx: The context object used for providing information updates during
        the execution of the function.
    :type ctx: Context
    :param typeOfCard: The type of card for which the CUNY Student ID should be
        fetched. Valid options are "getEmplidCard" or "getLibraryIdCard" or "both". Defaults
        to "getEmplidCard". If set to both, both types of cards will be fetched in one call
        no need to call the function twice.
    :return: A list containing an image with the path to the fetched card image
        and its format.
    :rtype: list[Image]
    """
    def get_image_path(image_name: str) -> list[Any] | list[Image] | list[TextContent]:
        if typeOfCard == "both":
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
        elif Path(os.getcwd() + f"/{typeOfCard}.png").exists():
            return [Image(path=os.getcwd() + f"/{typeOfCard}.png", format='png')]
        else:
            return [TextContent(type="text", text=f"No card(s) found")]

    await ctx.info("Fetching CUNY Student ID")
    result = get_image_path(typeOfCard)
    if result[0] is not TextContent:
        return result
    await ctx.info(
        "CUNY Student ID not found in cache, fetching CUNY Student ID"
    )
    results = await l360(headless=True, typeOfCard=typeOfCard)
    await ctx.info("CUNY Student ID fetched")
    return get_image_path(typeOfCard)


@cuny_info_mcp.tool(
    description="This function is used to search for courses on CUNY. It takes a query string as input and returns a dictionary containing the search results. DO NOT ASSUME A COURSE NUMBER IF A COURSE NUMBER IF a-zA-Z text is being used",
    title="Search Courses on CUNY",
    name="search_courses_on_cuny"
)
async def search_courses_on_cuny(ctx: Context, query: str):
    return await query_courses(query, ctx)


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
