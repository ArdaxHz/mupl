import base64
import json
import time
from configparser import SectionProxy
from typing import Optional

from requests import Session

from config import mangadex_auth_url


class OAuth2:
    def __init__(
        self,
        credential_config: "SectionProxy",
        client: "Session",
        access_token: "Optional[str]" = None,
        refresh_token: "Optional[str]" = None
    ):
        self.__username: "str" = credential_config["mangadex_username"]
        self.__password: "str" = credential_config["mangadex_password"]
        self.__client_id: "str" = credential_config["api_client_id"]
        self.__client_secret: "str" = credential_config["api_client_secret"]
        self.__client: "Session" = client
        self.__access_token: "Optional[str]" = access_token
        self.__refresh_token: "Optional[str]" = refresh_token

    def login(self):
        token_response = self.__client.post(
            url=f"{mangadex_auth_url}/token",
            data={
                "grant_type": "password",
                "username": self.__username,
                "password": self.__password,
                "client_id": self.__client_id,
                "client_secret": self.__client_secret,
            },
        ).json()
        self.__access_token = token_response["access_token"]
        self.__refresh_token = token_response["refresh_token"]

    def regenerate_access_token(self):
        token_response = self.__client.post(
            url=f"{mangadex_auth_url}/token",
            data={
                "grant_type": "refresh_token",
                "client_id": self.__client_id,
                "client_secret": self.__client_secret,
                "refresh_token": self.refresh_token,
            },
        ).json()
        self.__access_token = token_response["access_token"]
        self.__refresh_token = token_response["refresh_token"]

    @property
    def access_token(self) -> "str":
        assert self.__access_token is not None  # User not logged in
        return self.__access_token

    @property
    def access_token_expired(self) -> "bool":
        return self.__token_expired(self.access_token)

    @property
    def refresh_token(self) -> "str":
        assert self.__refresh_token is not None  # User not logged in
        return self.__refresh_token

    @property
    def refresh_token_expired(self) -> "bool":
        return self.__token_expired(self.refresh_token)

    @staticmethod
    def __token_expired(token: "str") -> "bool":
        payload_string = base64.b64decode(token.split(".")[1] + "===").decode("utf-8")
        expiry_time = json.loads(payload_string)["exp"]
        current_time = int(time.time())
        return (expiry_time - current_time) <= 0
