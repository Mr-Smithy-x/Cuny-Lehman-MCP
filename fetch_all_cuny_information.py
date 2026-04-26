import json
import os
import tracemalloc
from typing import Literal

from mcp.server.fastmcp import FastMCP, Context, Image

from cuny_core_functions import cuny_browser_login, l360

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
    await ctx.info("Fetching CUNY Student ID")
    results = await l360(headless=True, typeOfCard=typeOfCard)
    await ctx.info("CUNY Student ID fetched")
    if typeOfCard == "both":
        return [ Image(path=os.getcwd() + f"/getEmplidCard.png", format='png'), Image(path=os.getcwd() + f"/getLibraryIdCard.png", format='png') ]
    else:
        return [ Image(path=os.getcwd() + f"/{typeOfCard}.png", format='png') ]

if __name__ == "__main__":
    # Runs MCP server over stdio by default
    cuny_info_mcp.run()
