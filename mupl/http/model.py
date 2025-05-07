import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from configparser import ConfigParser

import requests

from mupl import __version__
from mupl.exceptions import MuplLoginError
from mupl.http import RequestError, http_error_codes
from mupl.http.response import HTTPResponse
from mupl.http.oauth import OAuth2


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
        mupl_path: Path,
        translation: Dict,
        cli: bool,
        **kwargs,
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": f"mupl/{__version__}"})

        self.upload_retry_total = upload_retry
        self.ratelimit_time = ratelimit_time
        self.mangadex_api_url = mangadex_api_url
        self.mdauth_path = mdauth_path
        self.mupl_path = mupl_path
        self.translation = translation
        self.cli = cli

        self.max_requests = 5
        self.number_of_requests = 0
        self.total_requests = 0
        self.total_not_login_row = 0
        self._token_file = self.mdauth_path

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
            self._file_token = self._open_auth_file()
            access_token = self._file_token.get("access_token")
            refresh_token = self._file_token.get("refresh_token")

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

        logger.debug(formatted_request_string)

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
                print(self.translation["logged_in"])
                self._first_login = False
            return True
        else:
            if not recursed:
                if self._token_file.exists():
                    logger.warning(f"Deleting mdauth file and trying again.")
                    self._token_file.unlink()
                    self._login(recursed=True)

        logger.critical("All login attempts failed.")
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
        """Update the session headers to include the auth token."""
        self.session.headers.update({"Authorization": f"Bearer {access_token}"})

    def _refresh_token_md(self) -> "bool":
        """Use the refresh token to get a new access token via OAuth client."""
        if self.refresh_token is None:
            logger.error(
                f"Refresh token doesn't exist, logging in through account details."
            )
            return self._login_using_details()

        logger.debug(f"Regenerating refresh token.")
        return self.oauth.regenerate_access_token()

    def _check_login(self) -> "bool":
        """Check if the current access token is valid using the /auth/check endpoint."""
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
        """Login using account details via OAuth client."""
        logger.debug(f"Logging in through account details.")
        return self.oauth.login()
