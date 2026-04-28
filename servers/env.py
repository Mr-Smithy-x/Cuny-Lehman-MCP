import dotenv
from pyotp import TOTP


def get_otp() -> tuple[str, str, str]:
    """
    login url
    https://ssologin.cuny.edu/oam/server/obrareq.cgi

    otp url
    https://ssologin.cuny.edu/oaa-totp-factor/rui/index.html
    """
    loc = dotenv.find_dotenv('../.env')
    env = dotenv.load_dotenv(loc)
    secret = str(dotenv.get_key(loc, "CUNY_TOPT"))
    email = str(dotenv.get_key(loc, "CUNY_EMAIL"))
    password = str(dotenv.get_key(loc, "CUNY_PASSWORD"))
    otp = TOTP(secret)
    toptime = otp.now()
    return email, password, toptime