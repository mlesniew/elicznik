"""Tauron eLicznik hourly energy readings: Python client and CLI."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("elicznik")
except PackageNotFoundError:  # running from a source checkout
    __version__ = "0.0.0"

from .client import Client
from .config import Credentials, load_credentials, read_env_file
from .errors import AuthError, ConfigError, ElicznikError, RateLimitError, ResponseError
from .models import Reading
from .parser import parse_csv

__all__ = [
    "AuthError",
    "Client",
    "ConfigError",
    "Credentials",
    "ElicznikError",
    "RateLimitError",
    "Reading",
    "ResponseError",
    "load_credentials",
    "parse_csv",
    "read_env_file",
]
