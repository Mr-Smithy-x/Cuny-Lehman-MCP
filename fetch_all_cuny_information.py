import asyncio
import json

from mcp.server.fastmcp import FastMCP, Context
from playwright.async_api import async_playwright
from pyotp import TOTP
from playwright.async_api import async_playwright
import asyncio
import dotenv
import tracemalloc

from test_cuny import cuny_browser_login

cuny_info_mcp = FastMCP("cuny-info-fetcher")


def get_otp():
    loc = dotenv.find_dotenv('.env')
    env = dotenv.load_dotenv(loc)
    secret = str(dotenv.get_key(loc, "CUNY_TOPT"))
    email = str(dotenv.get_key(loc, "CUNY_EMAIL"))
    password = str(dotenv.get_key(loc, "CUNY_PASSWORD"))
    otp = TOTP(secret)
    toptime = otp.now()
    return email, password, toptime


@cuny_info_mcp.tool(
    description="This is a server to fetch all cuny information such as financial tuition and cost, degree information and courses taking and current courses in progress. This function is an all in one function that should be used over the single functions as the single function takes too much time to fetch the information however this function is much quicker because it does everything all at once.",
    title="Fetch All Cuny Information",
    name="fetch_cuny_information"
)
async def fetch_cuny_information(
    ctx: Context,
    headless: bool = True,
) -> dict:
    tracemalloc.start()
    url = "http://cunyfirst.cuny.edu/"
    """
    Fetch fully JavaScript-rendered HTML from a URL.
    Returns a dict with status, html, and metadata for better AI parsing.
    """
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

if __name__ == "__main__":
    # Runs MCP server over stdio by default
    cuny_info_mcp.run()
