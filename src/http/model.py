import json
import logging
import time
from datetime import datetime

import requests

from src import __version__
from src.exceptions import MuplLoginError
from src.http import RequestError, http_error_codes
from src.http.response import HTTPResponse
from src.http.oauth import OAuth2
from src.utils.config import (
    UPLOAD_RETRY,
    config,
    mangadex_api_url,
    root_path,
    TRANSLATION,
)


logger = logging.getLogger("mupl")


class HTTPModel:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": f"mupl/{__version__}"})

        self.upload_retry_total = UPLOAD_RETRY
        self.max_requests = 5
        self.number_of_requests = 0
        self.total_requests = 0
        self.total_not_login_row = 0

        self._config = config
        self._token_file = root_path.joinpath(config["paths"]["mdauth_path"])
        self._file_token = self._open_auth_file()
        self._md_auth_api_url = f"{mangadex_api_url}/auth"

        self.oauth = OAuth2(
            self._config["credentials"],
            self,
            self._file_token.get("access"),
            self._file_token.get("refresh"),
        )

        self._first_login = True
        self._successful_login = False

    @property
    def access_token(self) -> "str":
        return self.oauth.access_token

    @property
    def refresh_token(self) -> "str":
        return self.oauth.refresh_token

    def _calculate_sleep_time(
        self, status_code: "int", wait: "bool", headers: "dict"
    ) -> "bool":
        self.number_of_requests += 1
        self.total_requests += 1
        loop = False

        limit = int(headers.get("x-ratelimit-limit", self.max_requests))
        remaining = int(
            headers.get(
                "x-ratelimit-remaining", self.max_requests - self.number_of_requests
            )
        )
        retry_after = headers.get("x-ratelimit-retry-after", None)

        logger.debug(f"limit: {limit}")
        logger.debug(f"remaining: {remaining}")
        logger.debug(f"retry_after: {retry_after}")
        logger.debug(f"number_of_requests: {self.number_of_requests}")

        delta = self.max_requests
        sleep = delta / limit
        if status_code == 429:
            error_message = f"429: {http_error_codes.get('429')}"
            logger.warning(error_message)
            sleep = 60
            loop = True

        if retry_after is not None:
            retry = datetime.fromtimestamp(int(retry_after))
            now = datetime.now()
            if retry > now:
                difference = retry - now
            else:
                difference = now - now

            delta = difference.total_seconds() + 1
            if remaining == 0:
                sleep = delta
                loop = True
            else:
                sleep = delta / remaining

        logger.debug("delta is: %s", delta)

        if remaining <= 0 or retry_after is not None or status_code == 429:
            if not wait and status_code != 429 and remaining > 0:
                return loop

            self.number_of_requests = 0
            logger.debug(f"Sleeping {sleep} seconds")
            time.sleep(sleep)

            if remaining == 0 and status_code != 429:
                loop = False
        return loop

    def _format_request_log(
        self,
        method: "str",
        route: "str",
        params: "dict" = None,
        json: "dict" = None,
        data=None,
        files=None,
        successful_codes: "list" = None,
    ) -> "str":
        return f'"{method}": {route} {successful_codes=} {params=} {json=} {data=}'

    def _request(
        self,
        method: "str",
        route: "str",
        params: "dict" = None,
        json: "dict" = None,
        data=None,
        files=None,
        successful_codes: "list" = None,
        **kwargs,
    ) -> "HTTPResponse":
        if successful_codes is None:
            successful_codes = []

        retry = self.upload_retry_total
        total_retry = self.upload_retry_total * 2
        run_number = 0
        tries = kwargs.get("tries", self.upload_retry_total)
        sleep = kwargs.get("sleep", True)

        formatted_request_string = self._format_request_log(
            method=method,
            route=route,
            params=params,
            json=json,
            data=data,
            files=files,
            successful_codes=successful_codes,
        )

        logger.info(formatted_request_string)

        while retry > 0:
            try:
                run_number += 1

                response = self.session.request(
                    method, route, json=json, params=params, data=data, files=files
                )
                logger.debug(
                    f"Initial Request: Code {response.status_code}, URL: {response.url}"
                )
                response_obj = HTTPResponse(response, successful_codes)

                if response.status_code == 401:
                    print(TRANSLATION["not_logged_in"])
                    self.total_not_login_row += 1
                    if self.total_not_login_row >= self.upload_retry_total:
                        return response_obj
                else:
                    self.total_not_login_row = 0

                loop = self._calculate_sleep_time(
                    status_code=response.status_code,
                    headers=response.headers,
                    wait=sleep,
                )

                retry -= 1
                total_retry -= 1
                if loop:
                    continue
            except requests.RequestException as e:
                logger.error(e)
                continue

            if (successful_codes and response.status_code not in successful_codes) or (
                response.status_code not in range(200, 300)
            ):
                response_obj.print_error()

            if response_obj.data is None and tries > 1 and total_retry > 0:
                continue

            if (
                (successful_codes and response.status_code in successful_codes)
                or (response.status_code in range(200, 300))
                or run_number == tries
            ) and response_obj.data is not None:
                return response_obj

            if response.status_code == 401:
                response_obj.print_error()
                try:
                    self._login()
                except Exception as e:
                    logger.error(e)

                    if total_retry <= 0:
                        break
                    retry = self.upload_retry_total
                    continue
            elif response.status_code == 429:
                response_obj.print_error()
                print(f"429: {http_error_codes.get('429')}")
                time.sleep(90)

                if total_retry <= 0:
                    break
                retry = self.upload_retry_total
                continue
            else:
                if tries == 1:
                    retry = 0

                response_obj.print_error(
                    show_error=kwargs.get("show_error", True),
                    log_error=kwargs.get("show_error", True),
                )
                continue

        raise RequestError(formatted_request_string)

    def _login(self, recursed=False) -> "bool":
        if self._first_login:
            logger.debug("Trying to login through the mdauth file.")

        if self.access_token is not None:
            self._update_headers(self.access_token)
            logged_in = self._check_login()
        else:
            logged_in = self._refresh_token_md()

        if logged_in:
            self._successful_login = True

            self._update_headers(self.access_token)
            self._save_tokens(self.access_token, self.refresh_token)

            if self._first_login:
                logger.info(f"Logged into mangadex.")
                print(TRANSLATION["logged_in"])
                self._first_login = False
            return True
        else:
            if not recursed:
                if self._token_file.exists():
                    logger.warning(f"Deleting mdauth file and trying again.")
                    self._token_file.unlink()
                    self._login(recursed=True)

            logger.critical("Couldn't login.")
            raise MuplLoginError("Couldn't login, check logs for error.")

    def _open_auth_file(self) -> "dict":
        """Open auth file and read saved tokens."""
        try:
            with open(self._token_file, "r") as login_file:
                token = json.load(login_file)
            return token
        except (FileNotFoundError, json.JSONDecodeError):
            logger.error(
                "Couldn't find the file, trying to login using your account details."
            )
            return {}

    def _save_tokens(self, access_token: "str", refresh_token: "str") -> None:
        """Save the access and refresh tokens."""
        with open(self._token_file, "w") as login_file:
            login_file.write(
                json.dumps({"access": access_token, "refresh": refresh_token}, indent=4)
            )
        logger.debug("Saved mdauth file.")

    def _update_headers(self, access_token: "str") -> None:
        """Update the access headers to include the auth token."""
        self.session.headers.update({"Authorization": f"Bearer {access_token}"})

    def _refresh_token_md(self) -> "bool":
        """Use the refresh token to get a new access token."""
        if self.refresh_token is None:
            logger.error(
                f"Refresh token doesn't exist, logging in through account details."
            )
            return self._login_using_details()

        logger.debug(f"Regenerating refresh token.")
        return self.oauth.regenerate_access_token()

    def _check_login(self) -> "bool":
        """Try login using saved access token."""
        try:
            auth_check_response = self._request(
                "GET",
                f"{self._md_auth_api_url}/check",
                successful_codes=[401, 403, 404],
                tries=1,
            )
        except RequestError as e:
            logger.error(e)
        else:
            if (
                auth_check_response.status_code == 200
                and auth_check_response.data is not None
            ):
                if auth_check_response.data["isAuthenticated"]:
                    logger.debug(
                        f"Already logged in: {auth_check_response.data['isAuthenticated']=}"
                    )
                    return True

        if self.refresh_token is None:
            return self._login_using_details()
        return self._refresh_token_md()

    def _login_using_details(self) -> "bool":
        """Login using account details."""
        logger.debug(f"Logging in through account details.")
        return self.oauth.login()
