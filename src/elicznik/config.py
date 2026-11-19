"""Credential loading: CLI flags > environment > .env file > interactive prompt."""

from __future__ import annotations

import getpass
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .const import ENV_PASSWORD, ENV_SITE, ENV_USERNAME, SITE_PATTERN
from .errors import ConfigError

DEFAULT_ENV_FILE = Path(".env")


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str = field(repr=False)
    site: str | None = None


def read_env_file(path: str | os.PathLike) -> dict[str, str]:
    """Parse a simple ``KEY=VALUE`` file (``export`` prefix, quotes and ``#`` comments allowed)."""
    result = {}
    for lineno, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = line.removeprefix("export ").lstrip()
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or not key:
            raise ConfigError(f"{path}:{lineno}: expected KEY=VALUE")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        result[key] = value
    return result


def validate_site(site: str | None) -> str | None:
    if not site:
        return None
    if not re.match(SITE_PATTERN, site):
        raise ConfigError(f"Invalid site {site!r}, expected format 123_456_789")
    return site


def load_credentials(
    *,
    username: str | None = None,
    site: str | None = None,
    env_file: str | os.PathLike | None = None,
    environ: Mapping[str, str] = os.environ,
    interactive: bool | None = None,
) -> Credentials:
    """Resolve credentials from arguments, environment, a .env file and, on a TTY, a prompt.

    ``env_file`` must exist when given explicitly; otherwise ``./.env`` is used if present.
    """
    if env_file is not None:
        if not Path(env_file).is_file():
            raise ConfigError(f"Env file not found: {env_file}")
        file_vars = read_env_file(env_file)
    elif DEFAULT_ENV_FILE.is_file():
        file_vars = read_env_file(DEFAULT_ENV_FILE)
    else:
        file_vars = {}

    def lookup(key: str) -> str | None:
        return environ.get(key) or file_vars.get(key) or None

    username = username or lookup(ENV_USERNAME)
    password = lookup(ENV_PASSWORD)
    site = validate_site(site or lookup(ENV_SITE))

    if interactive is None:
        interactive = sys.stdin.isatty()
    if interactive:
        if not username:
            print("Username: ", end="", file=sys.stderr, flush=True)
            username = input().strip()
        if not password:
            password = getpass.getpass()

    missing = [k for k, v in ((ENV_USERNAME, username), (ENV_PASSWORD, password)) if not v]
    if missing:
        raise ConfigError(f"Missing credentials: set {' and '.join(missing)} (environment or .env file)")
    return Credentials(username, password, site)
