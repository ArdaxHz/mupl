import json
import logging
import time
from copy import copy
from datetime import datetime
from typing import Optional

import requests

from uploader import __version__
from uploader.utils.config import mangadex_api_url, UPLOAD_RETRY, root_path, config

http_error_codes = {
    "400": "Bad Request.",
    "401": "Unauthorised.",
    "403": "Forbidden.",
    "404": "Not Found.",
    "429": "Too Many Requests.",
    "500": "Internal Server Error.",
    "502": "Bad Gateway.",
    "503": "Service Unavailable.",
    "504": "Gateway Timeout.",
}

logger = logging.getLogger("md_uploader")


class RequestError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class HTTPResponse:
    def __init__(self, response: requests.Response, successful_codes=None) -> None:
        if successful_codes is None:
            successful_codes = []
        else:
            successful_codes = copy(successful_codes)

        self.successful_codes = successful_codes.extend(range(200, 300))
        self.response = response
        self.data = self.json()

    @property
    def status_code(self):
        return self.response.status_code

    @property
    def status(self):
        return self.response.status_code

    @property
    def ok(self):
        return (
            True
            if self.response.ok or self.response.status_code in self.successful_codes
            else False
        )

    def json(self) -> Optional[dict]:
        """Convert the api response into a parsable json."""
        critical_decode_error_message = (
            f"{self.status_code}: Couldn't convert mangadex api response into a json."
        )

        logger.debug(f"Request id: {self.response.headers.get('x-request-id', None)}")

        if self.response.status_code == 204:
            return

        try:
            converted_response = self.response.json()
            return converted_response
        except json.JSONDecodeError:
            logger.critical(critical_decode_error_message)
            logger.error(self.response.content)
            print(critical_decode_error_message)
            return
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
                return

    def print_error(
        self,
        show_error: bool = False,
        log_error: bool = True,
    ) -> str:
        """Print the errors the site returns."""
        error_message = f"Error: {self.status_code}"
        error_json = self.json()

        if error_json is not None:
            # Api response doesn't follow the normal api error format
            try:
                errors = [
                    f'{e["status"]}: {e["detail"] if e["detail"] is not None else ""}'
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

        return error_message


class HTTPModel:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": f"md_uploader/{__version__}"})

        self.upload_retry_total = UPLOAD_RETRY
        self.max_requests = 5
        self.number_of_requests = 0
        self.total_requests = 0

        self._config = config
        self._token_file = root_path.joinpath(config["Paths"]["mdauth_path"])
        self._md_auth_api_url = f"{mangadex_api_url}/auth"
        self._md_auth_auth_url = f"{self._md_auth_api_url}/auth"
        self._md_auth_token_url = f"{self._md_auth_api_url}/token"
        self._md_auth_introspect_url = f"{self._md_auth_api_url}/introspect"
        self._file_token = self._open_auth_file()

        self._first_login = True
        self._successful_login = False
        self._session_token = self._file_token.get("session", None)
        self._refresh_token = self._file_token.get("refresh", None)

    def _calculate_sleep_time(self, status_code: int, wait: bool, headers):
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
        method: str,
        route: str,
        params: dict = None,
        json: dict = None,
        data=None,
        files=None,
        successful_codes: list = None,
    ):
        return f'"{method}": {route} {successful_codes=} {params=} {json=} {data=}'

    def _request(
        self,
        method: str,
        route: str,
        params: dict = None,
        json: dict = None,
        data=None,
        files=None,
        successful_codes: list = None,
        **kwargs,
    ):
        if successful_codes is None:
            successful_codes = []

        retry = self.upload_retry_total
        total_retry = self.upload_retry_total
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

        logger.debug(formatted_request_string)

        while retry > 0:
            try:
                response = self.session.request(
                    method, route, json=json, params=params, data=data, files=files
                )
                logger.debug(
                    f"Initial Request: Code {response.status_code}, URL: {response.url}"
                )

                loop = self._calculate_sleep_time(
                    status_code=response.status_code,
                    headers=response.headers,
                    wait=sleep,
                )
                if loop:
                    continue
            except requests.RequestException as e:
                logger.error(e)
                retry -= 1
                total_retry -= 1
                continue

            response_obj = HTTPResponse(response, successful_codes)
            if response_obj.data is None and tries > 1:
                retry -= 1
                continue

            if (successful_codes and response.status_code in successful_codes) or (
                response.status_code in range(200, 300)
            ):
                return response_obj

            if response.status_code == 401:
                error_message = f"401: Not logged in."
                logger.warning(error_message)
                print(error_message)
                try:
                    self._login()
                except Exception as e:
                    logger.error(e)

                    if total_retry >= 5:
                        break
                    retry = self.upload_retry_total
                    continue
            elif response.status_code == 429:
                error_message = f"429: {http_error_codes.get('429')}"
                logger.warning(error_message)
                print(error_message)
                time.sleep(60)

                if total_retry >= 5:
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
                retry -= 1
                total_retry -= 1
                continue

        raise RequestError(formatted_request_string)

    def _login(self):
        if self._first_login:
            logger.info("Trying to login through the .mdauth file.")

        if self._session_token is not None:
            logged_in = self._check_login()
        else:
            logged_in = self._refresh_token_md()

        if logged_in:
            self._successful_login = True
            if self._first_login:
                logger.info(f"Logged into mangadex.")
                print("Logged in.")
                self._first_login = False
        else:
            logger.critical("Couldn't login.")
            raise Exception("Couldn't login.")

    def _open_auth_file(self) -> dict:
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

    def _save_session(self, token: dict):
        """Save the session and refresh tokens."""
        with open(self._token_file, "w") as login_file:
            login_file.write(json.dumps(token, indent=4))
        logger.debug("Saved mdauth file.")

    def _update_headers(self, session_token: str):
        """Update the session headers to include the auth token."""
        self.session.headers.update({"Authorization": f"Bearer {session_token}"})

    def _update_token_details(self, token: dict):
        """Update the instance session and refresh tokens, update the header and save the file."""
        self._session_token = token["session"]
        self._refresh_token = token["refresh"]

        self._update_headers(token["session"])
        self._save_session(token)

    def _refresh_token_md(self) -> bool:
        """Use the refresh token to get a new session token."""
        refreshed = False

        if self._refresh_token is None:
            logger.error(
                f"Refresh token doesn't exist, logging in through account details."
            )
            return self._login_using_details()

        try:
            refresh_response = self._request(
                "POST",
                f"{self._md_auth_api_url}/refresh",
                json={"token": self._refresh_token},
                successful_codes=[401, 403],
                sleep=False,
            )
        except RequestError as e:
            logger.error(e)
            return False

        if refresh_response.status_code == 200 and refresh_response.data is not None:
            refresh_data = refresh_response.data["token"]
            self._update_token_details(refresh_data)
            return True
        elif refresh_response.status_code in (401, 403):
            logger.warning(
                f"Couldn't login using refresh token, logging in using your account."
            )
            return self._login_using_details()

        logger.error(f"Couldn't refresh token.")
        return refreshed

    def _check_login(self) -> bool:
        """Try login using saved session token."""
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
                    logger.info("Already logged in.")
                    return True

        if self._refresh_token is None:
            return self._login_using_details()
        return self._refresh_token_md()

    def _login_using_details(self) -> bool:
        """Login using account details."""
        username = self._config["MangaDex Credentials"]["mangadex_username"]
        password = self._config["MangaDex Credentials"]["mangadex_password"]

        if username == "" or password == "":
            critical_message = "Login details missing."
            logger.critical(critical_message)
            raise Exception(critical_message)

        try:
            login_response = self._request(
                "POST",
                f"{self._md_auth_api_url}/login",
                json={"username": username, "password": password},
                sleep=False,
                successful_codes=[401, 403, 404],
            )
        except RequestError as e:
            logger.error(e)
            return False

        if login_response.status_code == 200 and login_response.data is not None:
            login_token = login_response.data["token"]
            self._update_token_details(login_token)
            return True

        logger.error(f"Couldn't login to mangadex using the details provided.")
        return False


class HTTPClient(HTTPModel):
    def __init__(self):
        super().__init__()

    def request(
        self,
        method: str,
        route: str,
        params: dict = None,
        json: dict = None,
        data=None,
        files=None,
        successful_codes: list = None,
        **kwargs,
    ):
        return self._request(
            method=method,
            route=route,
            params=params,
            json=json,
            data=data,
            files=files,
            successful_codes=successful_codes,
            **kwargs,
        )

    def post(
        self,
        route: str,
        json: dict = None,
        data=None,
        files=None,
        successful_codes: list = None,
        **kwargs,
    ):
        return self._request(
            method="POST",
            route=route,
            json=json,
            data=data,
            files=files,
            successful_codes=successful_codes,
            **kwargs,
        )

    def get(
        self,
        route: str,
        params: dict = None,
        successful_codes: list = None,
        **kwargs,
    ):
        return self._request(
            method="GET",
            route=route,
            params=params,
            successful_codes=successful_codes,
            **kwargs,
        )

    def put(
        self,
        route: str,
        json: dict = None,
        data=None,
        files=None,
        successful_codes: list = None,
        **kwargs,
    ):
        return self._request(
            method="PUT",
            route=route,
            json=json,
            data=data,
            files=files,
            successful_codes=successful_codes,
            **kwargs,
        )

    def update(
        self,
        route: str,
        json: dict = None,
        data=None,
        files=None,
        successful_codes: list = None,
        **kwargs,
    ):
        return self.put(
            route=route,
            json=json,
            data=data,
            files=files,
            successful_codes=successful_codes,
            **kwargs,
        )

    def delete(
        self,
        route: str,
        params: dict = None,
        json: dict = None,
        data=None,
        successful_codes: list = None,
        **kwargs,
    ):
        return self._request(
            method="DELETE",
            route=route,
            params=params,
            json=json,
            data=data,
            successful_codes=successful_codes,
            **kwargs,
        )

    def login(self):
        """Login to MD account using details or saved token."""
        self._login()
