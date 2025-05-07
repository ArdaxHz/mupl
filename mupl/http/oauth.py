import base64
import json
import logging
import time
from configparser import SectionProxy
from typing import Optional, TYPE_CHECKING

logger = logging.getLogger("mupl")

if TYPE_CHECKING:
    from mupl.http.client import HTTPClient


class OAuth2:
    def __init__(
        self,
        credential_config: "SectionProxy",
        client: "HTTPClient",
        access_token: "Optional[str]" = None,
        refresh_token: "Optional[str]" = None,
        mangadex_auth_url: "str" = "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect",
    ):
        self.__client: "HTTPClient" = client
        self.__mangadex_auth_url = mangadex_auth_url
        self.token_url = f"{self.__mangadex_auth_url}/token"

        self.__username: "str" = credential_config.get("mangadex_username")
        self.__password: "str" = credential_config.get("mangadex_password")
        self.__client_id: "str" = credential_config.get("client_id")
        self.__client_secret: "str" = credential_config.get("client_secret")

        self.__access_token: "Optional[str]" = (
            None if self.__token_expired(access_token) else access_token
        )
        self.__refresh_token: "Optional[str]" = (
            None if self.__token_expired(refresh_token) else refresh_token
        )

    def __update_token(self, data: "dict"):
        """Update local vars with new tokens."""
        self.__access_token = data["access_token"]
        self.__refresh_token = data["refresh_token"]

    def login(self) -> "bool":
        """Generate access token from login and client details."""
        username = self.username
        password = self.password
        client_id = self.client_id
        client_secret = self.client_secret

        if not username or not password or not client_id or not client_secret:
            critical_message = "Login details missing."
            logger.critical(critical_message)
            raise Exception(critical_message)

        token_response = self.__client.post(
            self.token_url,
            data={
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            successful_codes=[401, 403, 404],
            tries=1,
        )

        if token_response.status_code == 200 and token_response.data is not None:
            self.__update_token(token_response.data)
            return True

        logger.error(f"Couldn't login to mangadex using the details provided.")
        return False

    def regenerate_access_token(self) -> "bool":
        """Regenerate access token using refresh token."""
        token_response = self.__client.post(
            self.token_url,
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
            },
            successful_codes=[401, 403, 404],
            tries=1,
        )

        if token_response.status_code == 200 and token_response.data is not None:
            self.__update_token(token_response.data)
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
    def username(self) -> "str":
        return self.__username

    @property
    def password(self) -> "str":
        return self.__password

    @property
    def client_id(self) -> "str":
        return self.__client_id

    @property
    def client_secret(self) -> "str":
        return self.__client_secret

    @staticmethod
    def __token_expired(token: "str") -> "bool":
        if not token:
            return True
        payload_string = base64.b64decode(token.split(".")[1] + "===").decode("utf-8")
        expiry_time = json.loads(payload_string)["exp"]
        current_time = int(time.time())
        return (expiry_time - current_time) <= 0
