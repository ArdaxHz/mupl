import json
import logging
from copy import copy
from pathlib import Path
from typing import Optional

from src.exceptions import MuplConfigNotFoundError, MuplLocalizationNotFoundError

logger = logging.getLogger("mupl")


root_path = Path(".")


def open_defaults_file(defaults_path: "Path") -> "dict":
    try:
        with open(
            defaults_path,
            "r",
            encoding="utf-8",
        ) as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_config_info(config: "dict", defaults: "dict"):
    """Check if the config file has the needed data, if not, use the default values."""
    for section in defaults:
        for option in defaults[section]:
            if option not in config[section] or not config[section].get(option):
                logger.debug(f"Using default value for config {section}: {option}")
                config[section][option] = defaults[section][option]

            if type(config[section][option]) != type(defaults[section][option]):
                config[section][option] = defaults[section][option]

            # Threads can't exceed default value
            if (
                config["options"]["number_threads"]
                >= defaults["options"]["number_threads"]
            ):
                config["options"]["number_threads"] = defaults["options"][
                    "number_threads"
                ]


def open_config_file(root_path: "Path") -> "dict":
    """Try to open the config file if it exists."""
    config_file_path = root_path.joinpath("config").with_suffix(".json")
    defaults_path = root_path.joinpath("src", "utils", "defaults").with_suffix(".json")
    defaults_file = open_defaults_file(defaults_path)

    if config_file_path.exists():
        config = json.loads(config_file_path.read_bytes())
    else:
        logger.critical("Config file not found, exiting.")
        raise MuplConfigNotFoundError("Config file not found.")

    load_config_info(config, defaults_file)
    return config


def read_localisation_file(path: "Path") -> "dict":
    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_localisation(lang: Optional["str"]):
    if not lang:
        lang = "en"

    lang = lang.lower()
    language_loc_dir = root_path.joinpath("src", "loc")
    language_json_path = language_loc_dir.joinpath(lang).with_suffix(".json")
    en_lang_json_path = language_loc_dir.joinpath("en").with_suffix(".json")

    en_localisation = read_localisation_file(en_lang_json_path)
    if not en_localisation:
        logger.exception(
            f"No localisation file found for {lang}, not running uploader."
        )
        raise MuplLocalizationNotFoundError(f"No localisation file found for {lang}.")

    if lang == "en":
        return en_localisation

    lang_localisation = read_localisation_file(language_json_path)
    if not lang_localisation:
        logger.error(f"No localisation file found for {lang}, using English.")

    localisation_merged = copy(lang_localisation)

    for option in en_localisation:
        if option not in lang_localisation or not lang_localisation.get(option):
            logger.debug(f"Using default value for localisation {option}")
            localisation_merged[option] = en_localisation[option]

    return localisation_merged


VERBOSE = False
config = open_config_file(root_path)

NUMBER_OF_IMAGES_UPLOAD = config["options"]["number_of_images_upload"]
UPLOAD_RETRY = config["options"]["upload_retry"]
RATELIMIT_TIME = config["options"]["ratelimit_time"]
MAX_LOG_DAYS = config["options"]["max_log_days"]
NUMBER_THREADS = config["options"]["number_threads"]
mangadex_api_url = config["paths"]["mangadex_api_url"]
mangadex_auth_url = config["paths"]["mangadex_auth_url"]
TRANSLATION = load_localisation(config["options"]["language"])
