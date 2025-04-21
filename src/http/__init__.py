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


class RequestError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
