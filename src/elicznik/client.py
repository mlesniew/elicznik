"""HTTP client for Tauron eLicznik."""

from __future__ import annotations

import html
import logging
import re
from datetime import date

import requests

from .config import Credentials, validate_site
from .const import BLOCK_PATH, DATA_URL, LOGIN_URL, SELECT_SITE_URL, SERVICE_URL, USER_AGENT
from .errors import AuthError, RateLimitError, ResponseError
from .models import Reading
from .parser import is_csv, parse_csv

_LOGGER = logging.getLogger(__name__)

_LOGIN_FORM_RE = re.compile(r'<form[^>]+id="kc-form-login"[^>]+action="([^"]+)"')
_RATE_LIMITED = "Przekroczono maksymalną liczbę logowań"


class Client:
    """Logs in to eLicznik and downloads hourly readings.

    Use as a context manager, or call :meth:`close` when done. Logging in is lazy:
    :meth:`readings` logs in on first use and once more if the session expires.
    """

    def __init__(
        self,
        username: str,
        password: str,
        site: str | None = None,
        *,
        session: requests.Session | None = None,
        timeout: float = 30,
    ):
        self._username = username
        self._password = password
        self._site = validate_site(site)
        self._timeout = timeout
        self._session = session or requests.Session()
        self._session.headers.setdefault("User-Agent", USER_AGENT)
        self._logged_in = False

    @classmethod
    def from_credentials(cls, credentials: Credentials, **kwargs) -> Client:
        return cls(credentials.username, credentials.password, credentials.site, **kwargs)

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._session.close()

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        try:
            resp = self._session.request(method, url, timeout=self._timeout, **kwargs)
        except requests.RequestException as err:
            raise ResponseError(f"Request to {url} failed: {err}") from err
        if resp.url.rstrip("/").endswith(BLOCK_PATH):
            raise RateLimitError("Tauron has temporarily blocked this account")
        if resp.status_code >= 500:
            raise ResponseError(f"Tauron returned HTTP {resp.status_code} for {url}")
        return resp

    def login(self) -> None:
        """Log in through Tauron's Keycloak form and select the metering point."""
        page = self._request("GET", LOGIN_URL, params={"service": SERVICE_URL}).text
        match = _LOGIN_FORM_RE.search(page)
        if match is None:
            raise ResponseError("Tauron login form not found")

        page = self._request(
            "POST",
            html.unescape(match.group(1)),
            data={"username": self._username, "password": self._password, "credentialId": ""},
        ).text
        if _RATE_LIMITED in page:
            raise RateLimitError("Too many login attempts, Tauron temporarily blocked logins")
        if 'id="kc-form-login"' in page:
            raise AuthError("Invalid Tauron username or password")

        if self._site:
            self._request("POST", SELECT_SITE_URL, data={"site[client]": self._site})
        self._logged_in = True
        _LOGGER.debug("Logged in to eLicznik")

    def _download_csv(self, start: date, end: date) -> str:
        params = {
            "form[from]": start.strftime("%d.%m.%Y"),
            "form[to]": end.strftime("%d.%m.%Y"),
            "form[type]": "godzin",
            "form[energy][consum]": "1",
            "form[energy][oze]": "1",
            "form[energy][netto]": "1",
            "form[energy][netto_oze]": "1",
            "form[fileType]": "CSV",
        }
        resp = self._request("GET", DATA_URL, params=params)
        return resp.content.decode("utf-8", errors="replace")

    def readings(self, start: date, end: date | None = None) -> list[Reading]:
        """Return hourly readings for local days ``start``..``end`` (inclusive)."""
        end = end or start
        if end < start:
            raise ValueError("end date is before start date")
        if not self._logged_in:
            self.login()
        text = self._download_csv(start, end)
        if not is_csv(text):
            _LOGGER.debug("Got non-CSV response, logging in again")
            self.login()
            text = self._download_csv(start, end)
        return [r for r in parse_csv(text) if start <= r.local_start.date() <= end]
