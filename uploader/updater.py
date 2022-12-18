import logging
import re

import requests

from . import __version__, root_path

logger = logging.getLogger("md_uploader")


def check_for_update():
    """Check For any program updates."""
    logger.debug("Looking for program update.")

    # Check the local version is the same as on GitHub
    remote_version_info_response = requests.get(
        "https://raw.githubusercontent.com/ArdaxHz/mangadex_bulk_uploader/main/md_uploader.py"
    )
    if remote_version_info_response.ok:
        remote_version_info = remote_version_info_response.content.decode()

        ver_regex = re.compile(r"^__version__\s=\s\"(.+)\"$", re.MULTILINE)
        match = ver_regex.search(remote_version_info)
        remote_number = match.group(1)

        local_version = float(
            f"{__version__.split('.')[0]}.{''.join(__version__.split('.')[1:])}"
        )
        remote_version = float(
            f"{remote_number.split('.')[0]}.{''.join(remote_number.split('.')[1:])}"
        )
        logger.warning(
            f"GitHub version: {remote_number}, local version: {__version__}."
        )

        if remote_version > local_version:
            download_update = input(
                f"""Looks like update {remote_number} is available, you're on {__version__}, do you want to download?
                "y" or "n" """
            ).strip()

            if download_update.lower() == "y":
                with open(
                        root_path.joinpath(f"{__file__}").with_suffix(".py"), "wb"
                ) as file:
                    file.write(remote_version_info_response.content)

                print(
                    "Downloaded the update, next program run will use the new update."
                )
                logger.info(
                    f"Successfully downloaded {remote_version}, will be used next program run."
                )
            else:
                print("Skipping update, this might result in api errors.")
                logger.warning("Update download skipped.")
    else:
        logger.error(
            f"Error searching for update: {remote_version_info_response.status_code}."
        )
