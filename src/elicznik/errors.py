"""Exception hierarchy. Each error carries the CLI exit code it maps to."""


class ElicznikError(Exception):
    """Base class for all elicznik errors."""

    exit_code = 1


class ConfigError(ElicznikError):
    """Missing or invalid configuration (credentials, site, dates)."""

    exit_code = 2


class AuthError(ElicznikError):
    """Tauron rejected the credentials."""

    exit_code = 3


class RateLimitError(ElicznikError):
    """Too many logins, or the account is temporarily blocked."""

    exit_code = 4


class ResponseError(ElicznikError):
    """Tauron returned something that could not be understood."""

    exit_code = 5
