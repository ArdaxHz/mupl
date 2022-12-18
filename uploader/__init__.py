from .utils import config
from .utils import root_path

__version__ = "1.0.0"

mangadex_api_url = config["Paths"]["mangadex_api_url"]
mangadex_auth_url = config["Paths"]["mangadex_auth_url"]
RATELIMIT_TIME = int(config["User Set"]["ratelimit_time"])
UPLOAD_RETRY = int(config["User Set"]["upload_retry"])
