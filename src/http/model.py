import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from configparser import ConfigParser

import requests

from src import __version__
from src.exceptions import MuplLoginError
from src.http import RequestError, http_error_codes
from src.http.response import HTTPResponse
from src.http.oauth import OAuth2


logger = logging.getLogger("mupl")


class HTTPModel:
    def __init__(
        self,
        mangadex_username: str,
        mangadex_password: str,
        client_id: str,
        client_secret: str,
        mangadex_auth_url: str,
        upload_retry: int,
        ratelimit_time: int,
        mangadex_api_url: str,
        mdauth_path: str,
        root_path: Path,
        translation: Dict,
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": f"mupl/{__version__}"})

        self.upload_retry_total = upload_retry
        self.ratelimit_time = ratelimit_time
        self.mangadex_api_url = mangadex_api_url
        self.mdauth_path = mdauth_path
        self.root_path = root_path
        self.translation = translation

        self.max_requests = 5
        self.number_of_requests = 0
        self.total_requests = 0
        self.total_not_login_row = 0

        self._token_file = self.root_path.joinpath(self.mdauth_path)
        credential_config = type(
            "SectionProxy",
            (),
            {
                "get": lambda self, key, fallback=None: {
                    "mangadex_username": mangadex_username,
                    "mangadex_password": mangadex_password,
                    "client_id": client_id,
                    "client_secret": client_secret,
                }.get(key, fallback)
            },
        )()

        access_token = None
        refresh_token = None

        if self._token_file.exists():
            try:
                config = ConfigParser()
                config.read(self._token_file)
                if "tokens" in config:
                    access_token = config["tokens"].get("access_token")
                    refresh_token = config["tokens"].get("refresh_token")
            except Exception as e:
                logger.warning(f"Failed to read auth tokens: {e}")

        self.oauth = OAuth2(
            credential_config,
            self,
            access_token,
            refresh_token,
            mangadex_auth_url=mangadex_auth_url,
        )

        self._md_auth_api_url = f"{self.mangadex_api_url}/auth"
        self._first_login = True
        self._successful_login = False

    @property
    def access_token(self) -> Optional[str]:
        return self.oauth.access_token

    @property
    def refresh_token(self) -> Optional[str]:
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
        sleep = delta / limit if limit > 0 else self.ratelimit_time
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

        if not route.startswith(("http://", "https://")):
            full_route = f"{self.mangadex_api_url}{route}"
        else:
            full_route = route

        formatted_request_string = self._format_request_log(
            method=method,
            route=full_route,
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
                    method, full_route, json=json, params=params, data=data, files=files
                )
                logger.debug(
                    f"Initial Request: Code {response.status_code}, URL: {response.url}"
                )

                response_obj = HTTPResponse(
                    response, self.translation, successful_codes
                )

                if response.status_code == 401:

                    print(self.translation.get("not_logged_in", "Not logged in."))
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

                retry = self.upload_retry_total
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

                    if not self._login():

                        logger.error("Re-login attempt failed.")

                        pass

                except Exception as e:
                    logger.error(f"Error during re-login attempt: {e}")

                    if total_retry <= 0:
                        break

                    retry = self.upload_retry_total
                    continue
            elif response.status_code == 429:
                response_obj.print_error()
                print(f"429: {http_error_codes.get('429')}")

                if total_retry <= 0:
                    break

                retry = self.upload_retry_total
                continue
            else:
                if tries == 1:
                    retry = 0

                response_obj.print_error(
                    show_error=kwargs.get("show_error", True),
                    log_error=kwargs.get("log_error", True),
                )

                continue

        raise RequestError(formatted_request_string)

    def _login(self, recursed=False) -> "bool":
        """Attempt to ensure the client is logged in."""
        if self._first_login:
            logger.debug("First login check.")

        if self.access_token:
            self._update_headers(self.access_token)
            if self._check_login_status():
                logger.debug("Already logged in and token is valid.")
                self._successful_login = True
                if self._first_login:

                    print(self.translation.get("logged_in", "Logged into MangaDex."))
                    self._first_login = False
                return True

        logger.debug("Access token invalid or missing, attempting refresh.")
        if self._refresh_token_md():
            logger.info("Successfully refreshed token.")
            self._successful_login = True
            self._update_headers(self.access_token)
            if self._first_login:

                print(self.translation.get("logged_in", "Logged into MangaDex."))
                self._first_login = False
            return True

        logger.warning(
            "Refresh token failed or missing, attempting login with credentials."
        )
        if self._login_using_details():
            logger.info("Successfully logged in using credentials.")
            self._successful_login = True
            self._update_headers(self.access_token)
            if self._first_login:

                print(self.translation.get("logged_in", "Logged into MangaDex."))
                self._first_login = False
            return True

        logger.critical("All login attempts failed.")

        raise MuplLoginError("Couldn't login, check logs for error.")

    def _update_headers(self, access_token: "str") -> None:
        """Update the session headers to include the auth token."""
        if access_token:
            self.session.headers.update({"Authorization": f"Bearer {access_token}"})
        else:

            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
        logger.debug("Updated session headers.")

    def _refresh_token_md(self) -> "bool":
        """Use the refresh token to get a new access token via OAuth client."""
        logger.debug("Attempting token refresh via OAuth client.")
        refreshed = self.oauth.regenerate_access_token()
        if refreshed:
            self._update_headers(self.oauth.access_token)
        return refreshed

    def _check_login_status(self) -> "bool":
        """Check if the current access token is valid using the /auth/check endpoint."""
        if not self.oauth.access_token:
            logger.debug("No access token found for status check.")
            return False

        self._update_headers(self.oauth.access_token)

        try:

            auth_check_response = self._request(
                "GET",
                f"{self._md_auth_api_url}/check",
                successful_codes=[401, 403, 404],
                tries=1,
                sleep=False,
            )

            if auth_check_response.ok and auth_check_response.data:
                is_authenticated = auth_check_response.data.get(
                    "isAuthenticated", False
                )
                logger.debug(f"/auth/check result: isAuthenticated={is_authenticated}")
                return is_authenticated
            else:
                logger.warning(
                    f"/auth/check request failed or returned unexpected data. Status: {auth_check_response.status_code}"
                )
                return False
        except RequestError as e:
            logger.error(f"Error during /auth/check request: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during login status check: {e}")
            return False

    def _login_using_details(self) -> "bool":
        """Login using account details via OAuth client."""
        logger.debug("Attempting login with credentials via OAuth client.")
        logged_in = self.oauth.login()
        if logged_in:
            self._update_headers(self.oauth.access_token)
        return logged_in
