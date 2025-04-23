import json
import os

import requests
from mupl.exceptions import MuplLocalizationNotFoundError
from mupl.utils.config import logger


from copy import copy
from pathlib import Path
from typing import Dict, Optional


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


def load_localisation(lang: Optional["str"] = None) -> Dict:
    """Load localization data for the specified language."""
    if not lang:
        lang = "en"

    lang = lang.lower()
    language_loc_dir = Path(os.path.abspath(__file__)).parent
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


def download_localisation(lang: Optional["str"] = None):
    if not lang:
        lang = "en"

    lang = lang.lower()
    loc_dir = Path(os.path.abspath(__file__)).parent
    language_json_path = loc_dir.joinpath(lang).with_suffix(".json")

    if language_json_path.exists():
        return load_localisation(lang)

    try:
        translation_url = (
            f"https://raw.githubusercontent.com/ArdaxHz/mupl/main/mupl/loc/{lang}.json"
        )
        logger.info(
            f"Attempting to download translation for {lang} from {translation_url}"
        )
        response = requests.get(translation_url)
        response.raise_for_status()

        with open(language_json_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        logger.info(f"Successfully downloaded translation for {lang}")
        return load_localisation(lang)
    except Exception as e:
        logger.warning(f"Failed to download translation for {lang}: {str(e)}")
        print(f"Failed to download translation for {lang}, falling back to English")

    return load_localisation("en")
