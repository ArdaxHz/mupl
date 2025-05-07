class MuplException(Exception):
    """Base class for all mupl exceptions."""

    pass


class MuplLoginError(MuplException):
    """Raised when login fails."""

    pass


class MuplOAuthError(MuplException):
    """Raised when OAuth token retrieval fails."""

    pass


class MuplConfigNotFoundError(MuplException, FileNotFoundError):
    """Raised when the configuration file is not found."""

    pass


class MuplLocalizationNotFoundError(MuplException, FileNotFoundError):
    """Raised when a required localization file is not found."""

    pass


class MuplUploadSessionError(MuplException):
    """Raised when there's an error managing an upload session."""

    pass


class MuplValidationError(MuplException):
    """Raised when a file fails validation."""

    pass


class MuplNotAFileError(MuplException):
    """Raised when a path is not a file."""

    pass
