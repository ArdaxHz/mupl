import json
import logging
import sys
from copy import copy
from pathlib import Path
from typing import Optional, Dict

from src.exceptions import MuplLocalizationNotFoundError

logger = logging.getLogger("mupl")


def open_defaults_file(defaults_path: "Path") -> "dict":
    """Load default configuration values from a file."""
    try:
        with open(
            defaults_path,
            "r",
            encoding="utf-8",
        ) as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def read_localisation_file(path: "Path") -> "dict":
    """Read a localization file and return its contents as a dictionary."""
    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_localisation(root_path: Path, lang: Optional["str"] = None) -> Dict:
    """Load localization data for the specified language."""
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


def load_config(config_path, cli=False):
    """Load configuration from file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        if cli:
            print(f"Error: Configuration file not found at {config_path}")
            sys.exit(1)
        else:
            raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {config_path}: {e}")
        if cli:
            print(f"Error: Invalid JSON in configuration file: {config_path}: {e}")
            sys.exit(1)
        else:
            raise
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        if cli:
            print(f"Error loading configuration: {e}")
            sys.exit(1)
        else:
            raise
