from datetime import date

import pytest
import requests

from elicznik import AuthError, Client, RateLimitError

LOGIN_PAGE = '<form id="kc-form-login" class="x" action="https://login/auth?a=1&amp;b=2" method="post">'
CSV = "Data;Strefa;Wartość;Rodzaj;Status;\n2026-11-19 1:00;T3;0,171;pobór [kWh]; licznik; \n2026-11-20 1:00;T3;0,2;pobór [kWh]; licznik; \n"


class FakeResponse:
    def __init__(self, text, url="https://elicznik.tauron-dystrybucja.pl/", status=200):
        self.text, self.url, self.status_code, self.content = text, url, status, text.encode()


class FakeSession(requests.Session):
    def __init__(self, responses):
        super().__init__()
        self.responses, self.calls = list(responses), []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


def test_login_and_fetch_filters_to_requested_days():
    s = FakeSession([FakeResponse(LOGIN_PAGE), FakeResponse("ok"), FakeResponse(CSV)])
    with Client("u", "p", session=s) as c:
        readings = c.readings(date(2026, 11, 19))
    assert [r.consumption for r in readings] == [0.171]
    assert s.calls[1][1] == "https://login/auth?a=1&b=2"


def test_relogin_when_session_expired():
    s = FakeSession([FakeResponse(LOGIN_PAGE), FakeResponse("ok"), FakeResponse("<html>"),
                     FakeResponse(LOGIN_PAGE), FakeResponse("ok"), FakeResponse(CSV)])
    assert len(Client("u", "p", session=s).readings(date(2026, 11, 19), date(2026, 11, 20))) == 2


def test_bad_password():
    s = FakeSession([FakeResponse(LOGIN_PAGE), FakeResponse(LOGIN_PAGE)])
    with pytest.raises(AuthError):
        Client("u", "p", session=s).login()


def test_blocked():
    s = FakeSession([FakeResponse("", url="https://elicznik.tauron-dystrybucja.pl/blokada")])
    with pytest.raises(RateLimitError):
        Client("u", "p", session=s).login()
