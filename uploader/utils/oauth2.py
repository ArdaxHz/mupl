import base64
import json
import logging
import time
from configparser import SectionProxy
from typing import Optional, TYPE_CHECKING

from requests import Session

from uploader.utils.config import mangadex_auth_url

logger = logging.getLogger("md_uploader")

if TYPE_CHECKING:
    from uploader.http import HTTPClient


class OAuth2:
    def __init__(
        self,
        credential_config: "SectionProxy",
        client: "HTTPClient",
        access_token: "Optional[str]" = None,
        refresh_token: "Optional[str]" = None,
    ):
        self.__username: "str" = credential_config.get("mangadex_username", "")
        self.__password: "str" = credential_config.get("mangadex_password", "")
        self.__client_id: "str" = credential_config.get("client_id", "")
        self.__client_secret: "str" = credential_config.get("client_secret", "")
        self.__client: "HTTPClient" = client
        self.__access_token: "Optional[str]" = access_token
        self.__refresh_token: "Optional[str]" = refresh_token

    def login(self):
        token_response = self.__client.post(
            f"{mangadex_auth_url}/token",
            data={
                "grant_type": "password",
                "username": self._username,
                "password": self._password,
                "client_id": self.__client_id,
                "client_secret": self.__client_secret,
            },
        )

        if token_response.status_code == 200 and token_response.data is not None:
            token_response_json = token_response.data
            self.__access_token = token_response_json["access_token"]
            self.__refresh_token = token_response_json["refresh_token"]
            return True

        logger.error(f"Couldn't login to mangadex using the details provided.")
        return False

    def regenerate_access_token(self):
        token_response = self.__client.post(
            f"{mangadex_auth_url}/token",
            data={
                "grant_type": "refresh_token",
                "client_id": self.__client_id,
                "client_secret": self.__client_secret,
                "refresh_token": self.refresh_token,
            },
        )

        if token_response.status_code == 200 and token_response.data is not None:
            token_response_json = token_response.data
            self.__access_token = token_response_json["access_token"]
            self.__refresh_token = token_response_json["refresh_token"]
            return True
        elif token_response.status_code in (401, 403):
            logger.warning(
                f"Couldn't login using refresh token, logging in using your account."
            )
            return self.login()

        logger.error(f"Couldn't refresh token.")
        return False

    @property
    def access_token(self) -> "str":
        return self.__access_token

    @property
    def access_token_expired(self) -> "bool":
        return self.__token_expired(self.access_token)

    @property
    def refresh_token(self) -> "str":
        return self.__refresh_token

    @property
    def refresh_token_expired(self) -> "bool":
        return self.__token_expired(self.refresh_token)

    @property
    def username(self):
        return self.__username

    @property
    def password(self):
        return self.__password

    @property
    def client_id(self):
        return self.__client_id

    @property
    def client_secret(self):
        return self.__client_secret

    @staticmethod
    def __token_expired(token: "str") -> "bool":
        payload_string = base64.b64decode(token.split(".")[1] + "===").decode("utf-8")
        expiry_time = json.loads(payload_string)["exp"]
        current_time = int(time.time())
        return (expiry_time - current_time) <= 0
