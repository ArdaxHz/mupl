import configparser
import logging
from pathlib import Path

logger = logging.getLogger("md_uploader")


root_path = Path(".")


def load_config_info(config: "configparser.RawConfigParser"):
    """Check if the config file has the needed data, if not, use the default values."""
    if config["Paths"].get("mangadex_api_url", "") == "":
        logger.warning("Mangadex api path empty, using default.")
        config["Paths"]["mangadex_api_url"] = "https://api.mangadex.org"

    if config["Paths"].get("mangadex_auth_url", "") == "":
        logger.warning("Mangadex auth path empty, using default.")
        config["Paths"][
            "mangadex_auth_url"
        ] = "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect"

    if config["Paths"].get("name_id_map_file", "") == "":
        logger.info("Name id map_file path empty, using default.")
        config["Paths"]["name_id_map_file"] = "name_id_map.json"

    if config["Paths"].get("uploads_folder", "") == "":
        logger.info("To upload files folder path empty, using default.")
        config["Paths"]["uploads_folder"] = "to_upload"

    if config["Paths"].get("uploaded_files", "") == "":
        logger.info("Uploaded files folder path empty, using default.")
        config["Paths"]["uploaded_files"] = "uploaded"

    if config["Paths"].get("mdauth_path", "") == "":
        logger.info("mdauth path empty, using default.")
        config["Paths"]["mdauth_path"] = ".mdauth"

    # Config files can only take strings, convert all the integers to string.


def open_config_file(root_path: "Path") -> "configparser.RawConfigParser":
    """Try to open the config file if it exists."""
    config_file_path = root_path.joinpath("config").with_suffix(".ini")
    # Open config file and read values
    if config_file_path.exists():
        config = configparser.RawConfigParser()
        config.read(config_file_path)
        logger.info("Loaded config file.")
    else:
        logger.critical("Config file not found, exiting.")
        raise FileNotFoundError("Config file not found.")

    load_config_info(config)
    return config


config = open_config_file(root_path)

try:
    NUMBER_OF_IMAGES_UPLOAD = int(config["User Set"].get("number_of_images_upload", ""))
except ValueError:
    logger.warning(
        "Config file number of images to upload is empty or contains a non-number character, using default of 10."
    )
    NUMBER_OF_IMAGES_UPLOAD = 10

try:
    UPLOAD_RETRY = int(config["User Set"].get("upload_retry", ""))
except ValueError:
    logger.warning(
        "Config file number of image retry is empty or contains a non-number character, using default of 3."
    )
    UPLOAD_RETRY = 3

try:
    RATELIMIT_TIME = int(config["User Set"].get("ratelimit_time", ""))
except (ValueError, KeyError):
    logger.warning(
        "Config file time to sleep is empty or contains a non-number character, using default of 2."
    )
    RATELIMIT_TIME = 2

try:
    MAX_LOG_DAYS = int(config["User Set"].get("max_log_days", ""))
except (ValueError, KeyError):
    logger.warning(
        "Config max days to keep logs is empty or contains a non-number character, using default of 30."
    )
    MAX_LOG_DAYS = 30

mangadex_api_url = config["Paths"]["mangadex_api_url"]
mangadex_auth_url = config["Paths"]["mangadex_auth_url"]
