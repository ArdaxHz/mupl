import json
import logging
from copy import copy
from typing import Optional

import requests

from mupl.http import http_error_codes


logger = logging.getLogger("mupl")


class HTTPResponse:
    def __init__(
        self,
        response: "requests.Response",
        translation: dict,
        successful_codes: "list" = None,
    ) -> None:
        if isinstance(successful_codes, list):
            successful_codes = copy(successful_codes)
        else:
            successful_codes = []

        successful_codes.extend(range(200, 300))
        self.successful_codes = successful_codes
        self.response = response
        self.translation = translation
        self.data = self.json()

    @property
    def status_code(self) -> "int":
        return self.response.status_code

    @property
    def status(self) -> "int":
        return self.status_code

    @property
    def ok(self) -> "bool":
        return (
            True
            if self.response.ok or self.response.status_code in self.successful_codes
            else False
        )

    def json(self) -> "Optional[dict]":
        """Convert the api response into a parsable json."""

        critical_decode_error_message = self.translation.get(
            "unable_convert_api_response_to_json",
            "Unable to convert api response {0} to json.",
        ).format(self.status_code)

        logger.info(f"Request id: {self.response.headers.get('x-request-id', None)}")

        if self.response.status_code == 204:
            return None

        try:
            converted_response = self.response.json()
            return converted_response
        except json.JSONDecodeError:
            logger.critical(critical_decode_error_message)
            logger.error(self.response.content)
            print(critical_decode_error_message)
            return None
        except AttributeError:
            logger.critical(
                f"Api response doesn't have load as json method, trying to load as json manually."
            )
            try:
                converted_response = json.loads(self.response.content)
                return converted_response
            except json.JSONDecodeError:
                logger.critical(critical_decode_error_message)
                logger.error(self.response.content)
                print(critical_decode_error_message)
                return None

    def print_error(
        self,
        show_error: "bool" = False,
        log_error: "bool" = True,
    ) -> "str":
        """Print the errors the site returns."""
        if self.ok:
            return None

        error_message = f"Error: {self.status_code}"
        error_json = self.json()

        if error_json is not None:
            try:
                errors = [
                    f'{e["status"]}: {e["title"]}: {e["detail"] if e["detail"] is not None else ""}'
                    for e in error_json["errors"]
                ]
                errors = ", ".join(errors)

                if not errors:
                    errors = http_error_codes.get(str(self.status_code), "")

                error_message = f"Error: {errors}"
                if log_error:
                    logger.warning(error_message)
                if show_error:
                    print(error_message)
            except KeyError:
                error_message = f"KeyError {self.status_code}: {error_json}."
                if log_error:
                    logger.warning(error_message)
                if show_error:
                    print(error_message)
        else:
            logger.error(self.response.content)

        return error_message
