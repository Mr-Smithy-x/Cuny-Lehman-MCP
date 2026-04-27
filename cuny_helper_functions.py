import json
from datetime import datetime
from typing import Literal

import dotenv
import requests
from playwright.async_api import Page, async_playwright
from pyotp import TOTP

def get_otp() -> tuple[str, str, str]:
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
    return email, password, toptime

def get_current_term_via_time():
    """
    Get the current term based on the current date and time.

    Determines the semester based on the current month:
    - January to May: Spring semester
    - June to August: Summer semester
    - September to December: Fall semester

    :return: The section code for the current term.
    :rtype: int
    """
    now = datetime.now()
    year = now.year
    month = now.month

    # Determine semester based on current month
    if 1 <= month <= 5:
        semester = "spring"
    elif 6 <= month <= 8:
        semester = "summer"
    else:  # 9 <= month <= 12
        semester = "fall"

    return resolve_section_code(year, semester)


def get_current_term(college: Literal["leh01"] = "leh01"):

    try:
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
    except Exception as e:
        return {"id": str(get_current_term_via_time())}

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

def parse_section_code(section_code: str) -> tuple[int, str]:
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

def search_course_catalog(query: str, catalog: str, college: Literal["leh01"] = "leh01"):

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

async def get_active_catalog(page: Page):
    await page.goto("https://lehman-graduate.catalog.cuny.edu/courses", wait_until="domcontentloaded")
    active_catalog = await page.evaluate("this.__NUXT__.state.settings.activeCatalog")
    return active_catalog


async def search_courses(query: str, college: Literal["leh01"] = "leh01"):

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        catalog = await get_active_catalog(page)
        result = search_course_catalog(query=query, catalog=catalog, college=college)
        await browser.close()
        return result