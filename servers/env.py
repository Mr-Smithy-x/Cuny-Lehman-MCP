import dotenv
from pyotp import TOTP


def get_lm_studio_default_model():
    return get_env_variable("LM_STUDIO_MODEL")

def get_lm_studio_host_scheme():
    return get_env_variable("LM_STUDIO_HOST_SCHEME")

def get_lm_studio_host_address():
    return get_env_variable("LM_STUDIO_HOST_ADDRESS")

def get_lm_studio_host_port():
    return get_env_variable("LM_STUDIO_HOST_PORT")

def get_lm_studio_api_key():
    return get_env_variable("LM_STUDIO_API_KEY")

def get_env_variable(key: str) -> str:
    loc = dotenv.find_dotenv('../.env')
    env = dotenv.load_dotenv(loc)
    value = str(dotenv.get_key(loc, key))
    return value

def get_otp() -> tuple[str, str, str]:
    """
    login url
    https://ssologin.cuny.edu/oam/server/obrareq.cgi

    otp url
    https://ssologin.cuny.edu/oaa-totp-factor/rui/index.html
    """
    secret = get_env_variable("CUNY_TOPT")
    email = get_env_variable("CUNY_EMAIL")
    password = get_env_variable("CUNY_PASSWORD")
    otp = TOTP(secret)
    toptime = otp.now()
    return email, password, toptime