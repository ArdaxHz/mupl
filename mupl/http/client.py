import logging
from pathlib import Path
from typing import Optional, Dict

from mupl.http.model import HTTPModel
from mupl.http.response import HTTPResponse

logger = logging.getLogger("mupl")


class HTTPClient(HTTPModel):
    def __init__(
        self,
        mangadex_username: Optional[str] = None,
        mangadex_password: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        mangadex_api_url: str = "https://api.mangadex.org",
        mangadex_auth_url: str = "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect",
        mdauth_path: str = ".mdauth",
        ratelimit_time: int = 2,
        upload_retry: int = 3,
        translation: Optional[Dict] = None,
        mupl_path: Path = Path("."),
        cli: bool = False,
        **kwargs,
    ):
        """Initialize the HTTP client with credentials and configuration."""
        super().__init__(
            mangadex_username=mangadex_username,
            mangadex_password=mangadex_password,
            client_id=client_id,
            client_secret=client_secret,
            mangadex_auth_url=mangadex_auth_url,
            upload_retry=upload_retry,
            ratelimit_time=ratelimit_time,
            mangadex_api_url=mangadex_api_url,
            mdauth_path=mdauth_path,
            mupl_path=mupl_path,
            translation=translation,
            cli=cli,
            **kwargs,
        )

    def request(
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
        if not route.startswith(("http://", "https://", "/")):
            route = f"/{route}"
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
        route: "str",
        json: "dict" = None,
        data=None,
        files=None,
        successful_codes: "list" = None,
        **kwargs,
    ) -> "HTTPResponse":
        if not route.startswith(("http://", "https://", "/")):
            route = f"/{route}"
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
        route: "str",
        params: "dict" = None,
        successful_codes: "list" = None,
        **kwargs,
    ) -> "HTTPResponse":
        if not route.startswith(("http://", "https://", "/")):
            route = f"/{route}"
        return self._request(
            method="GET",
            route=route,
            params=params,
            successful_codes=successful_codes,
            **kwargs,
        )

    def put(
        self,
        route: "str",
        json: "dict" = None,
        data=None,
        files=None,
        successful_codes: "list" = None,
        **kwargs,
    ) -> "HTTPResponse":
        if not route.startswith(("http://", "https://", "/")):
            route = f"/{route}"
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
        route: "str",
        json: "dict" = None,
        data=None,
        files=None,
        successful_codes: "list" = None,
        **kwargs,
    ) -> "HTTPResponse":
        if not route.startswith(("http://", "https://", "/")):
            route = f"/{route}"

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
        route: "str",
        params: "dict" = None,
        json: "dict" = None,
        data=None,
        successful_codes: "list" = None,
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
        return self._login()
