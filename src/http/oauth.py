import json
import logging
from configparser import SectionProxy
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import requests

from src.exceptions import MuplLoginError

if TYPE_CHECKING:
    from src.http.client import HTTPClient


logger = logging.getLogger("mupl")


class OAuth2:
    def __init__(
        self,
        config: "SectionProxy",
        client: "HTTPClient",
        access_token: "Optional[str]" = None,
        refresh_token: "Optional[str]" = None,
        mangadex_auth_url: str = "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect",
    ):
        self.config = config
        self.client = client
        self.access_token = access_token
        self.refresh_token = refresh_token

        self.mangadex_auth_url = mangadex_auth_url

        self.token_url = f"{self.mangadex_auth_url}/token"

        self._token_file = self.client.root_path.joinpath(self.client.mdauth_path)

    def _save_tokens(self) -> None:
        """Save the current access and refresh tokens to the mdauth file."""
        if self.access_token and self.refresh_token:
            try:
                with open(self._token_file, "w") as login_file:

                    token_data = {
                        "access": self.access_token,
                        "refresh": self.refresh_token,
                    }
                    json.dump(token_data, login_file, indent=4)
                logger.debug(f"Saved tokens to {self._token_file}")
            except IOError as e:
                logger.error(f"Failed to save tokens to {self._token_file}: {e}")
        else:
            logger.warning("Attempted to save tokens, but one or both were missing.")

    def login(self) -> "bool":
        """Login using account details."""
        logger.debug("Attempting login with credentials.")
        data = {
            "grant_type": "password",
            "username": self.config.get("mangadex_username"),
            "password": self.config.get("mangadex_password"),
            "client_id": self.config.get("client_id"),
            "client_secret": self.config.get("client_secret"),
        }

        try:

            response = self.client.session.post(self.token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")

            if self.access_token and self.refresh_token:
                logger.info("Successfully logged in with credentials.")
                self._save_tokens()
                return True
            else:
                logger.error(
                    "Login request succeeded but tokens were missing in response."
                )
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Login request failed: {e}")

            if hasattr(e, "response") and e.response is not None:
                logger.error(
                    f"Response status: {e.response.status_code}, Body: {e.response.text}"
                )
                if e.response.status_code == 401:
                    raise MuplLoginError("Invalid credentials provided.") from e
                elif e.response.status_code == 400:

                    raise MuplLoginError(
                        f"Bad request during login (check client ID/secret?): {e.response.text}"
                    ) from e
            raise MuplLoginError(f"Network or server error during login: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode login response JSON: {e}")
            raise MuplLoginError("Invalid response received from auth server.") from e

    def regenerate_access_token(self) -> "bool":
        """Use the refresh token to get a new access token."""
        if not self.refresh_token:
            logger.error("Refresh token is missing, cannot regenerate access token.")
            return False

        logger.debug("Attempting to regenerate access token using refresh token.")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.config.get("client_id"),
            "client_secret": self.config.get("client_secret"),
        }
        try:

            response = self.client.session.post(self.token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data.get("access_token")

            new_refresh_token = token_data.get("refresh_token")
            if new_refresh_token:
                self.refresh_token = new_refresh_token

            if self.access_token:
                logger.info("Successfully refreshed access token.")
                self._save_tokens()
                return True
            else:
                logger.error(
                    "Token refresh request succeeded but access token was missing."
                )

                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Token refresh request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(
                    f"Response status: {e.response.status_code}, Body: {e.response.text}"
                )

                if e.response.status_code in [400, 401]:
                    logger.warning("Refresh token seems invalid. Clearing tokens.")
                    self.access_token = None
                    self.refresh_token = None
                    self._token_file.unlink(missing_ok=True)

            return False
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode token refresh response JSON: {e}")
            return False
