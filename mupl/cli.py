import sys
import logging
import argparse
from pathlib import Path

from mupl import Mupl
from mupl.loc.load import load_localisation
from mupl.updater import check_for_update
from mupl.exceptions import MuplException
from mupl.utils.config import load_config
from mupl.utils.logs import setup_logs, clear_old_logs, format_log_dir_path

logger = logging.getLogger("mupl")


def main():
    parser = argparse.ArgumentParser(description="MangaDex Upload Tool")

    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to the configuration file.",
    )
    parser.add_argument(
        "--update",
        "-u",
        action="store_true",
        help="Check for program update before running.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase log verbosity (e.g., -v for DEBUG).",
    )
    parser.add_argument(
        "--threaded",
        "-t",
        action="store_true",
        help="Upload the images concurrently using threads.",
    )
    parser.add_argument(
        "--combine",
        "-c",
        action="store_true",
        help="Combine images less than 120px height with adjacent taller images.",
    )
    parser.add_argument(
        "--widestrip",
        "-w",
        action="store_true",
        help="Treat chapters as widestrip images, splitting based on width.",
    )
    parser.add_argument(
        "--dir",
        "-d",
        type=str,
        default=None,
        help="Specify the directory to upload from, overriding the config file setting.",
    )

    vargs = vars(parser.parse_args())

    mupl_path = Path(".")
    log_folder_path = format_log_dir_path(mupl_path)
    verbose_level = vargs.get("verbose", 0)
    setup_logs(
        logger_name="mupl",
        path=log_folder_path,
        logger_filename="mupl",
        level=verbose_level,
    )

    config_path = vargs.get("config")
    config_data = load_config(config_path, cli=True)

    language = config_data.get("options", {}).get("language", "en")
    translation = load_localisation(language)

    if vargs.get("update", True):
        try:
            mdauth_path = config_data.get("paths", {}).get("mdauth_path", ".mdauth")
            updated = check_for_update(
                mupl_path=mupl_path,
                translation=translation,
                mdauth_path=mdauth_path,
            )
        except Exception as e:
            logger.exception("Update check failed.")
            print("Not updating due to error.")

    try:
        max_log_days = config_data.get("options", {}).get("max_log_days", 30)
        log_folder_path = format_log_dir_path(mupl_path)
        clear_old_logs(log_folder_path, max_log_days)

        number_threads = config_data["options"]["number_threads"]
        uploaded_files = config_data["paths"]["uploaded_files"]
        ratelimit_time = config_data["options"]["ratelimit_time"]
        widestrip = vargs.get("widestrip", False)
        combine = vargs.get("combine", False)

        mupl = Mupl(
            mangadex_username=config_data["credentials"]["mangadex_username"],
            mangadex_password=config_data["credentials"]["mangadex_password"],
            client_id=config_data["credentials"]["client_id"],
            client_secret=config_data["credentials"]["client_secret"],
            number_of_images_upload=config_data["options"]["number_of_images_upload"],
            upload_retry=config_data["options"]["upload_retry"],
            ratelimit_time=ratelimit_time,
            max_log_days=config_data["options"]["max_log_days"],
            group_fallback_id=config_data["options"]["group_fallback_id"],
            number_threads=number_threads,
            language=config_data["options"]["language"],
            name_id_map_filename=config_data["paths"]["name_id_map_file"],
            uploaded_dir_path=uploaded_files,
            mangadex_api_url=config_data["paths"]["mangadex_api_url"],
            mangadex_auth_url=config_data["paths"]["mangadex_auth_url"],
            mdauth_filename=config_data["paths"]["mdauth_path"],
            translation=translation,
            cli=True,
            move_files=True,
            verbose_level=verbose_level,
            verbose=False,
        )

        upload_dir = vargs.get("dir")
        upload_directory_path = (
            Path(upload_dir)
            if upload_dir
            else Path(config_data["paths"]["uploads_folder"])
        )
        upload_directory_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using specified upload directory: {upload_directory_path}")

        failed_list = mupl.upload_directory(
            upload_directory_path,
            widestrip=widestrip,
            combine=combine,
        )
        sys.exit(1 if failed_list else 0)
    except (Exception, MuplException) as e:
        logger.exception(f"An unexpected error occurred: {e}")
        print(f"Error: An unexpected error occurred: {e}")
        sys.exit(1)
