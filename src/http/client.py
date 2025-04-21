from src.http.model import HTTPModel


class HTTPClient(HTTPModel):
    def __init__(self):
        super().__init__()

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
        route: "str",
        json: "dict" = None,
        data=None,
        files=None,
        successful_codes: "list" = None,
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
        route: "str",
        params: "dict" = None,
        successful_codes: "list" = None,
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
        route: "str",
        json: "dict" = None,
        data=None,
        files=None,
        successful_codes: "list" = None,
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
        route: "str",
        json: "dict" = None,
        data=None,
        files=None,
        successful_codes: "list" = None,
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
