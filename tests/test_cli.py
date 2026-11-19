from datetime import date, timedelta

import pytest

from elicznik import cli
from elicznik.errors import ConfigError


@pytest.fixture(autouse=True)
def no_credentials(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for k in ("ELICZNIK_USERNAME", "ELICZNIK_PASSWORD", "ELICZNIK_SITE"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False, raising=False)


def test_missing_credentials_exit_code(capsys, caplog):
    assert cli.run([]) == 2
    assert capsys.readouterr().out == ""
    assert "ELICZNIK_PASSWORD" in caplog.text


def test_date_range_days():
    args = cli.build_parser().parse_args(["--days", "3"])
    yesterday = date.today() - timedelta(days=1)
    assert cli._date_range(args) == (yesterday - timedelta(days=2), yesterday)


def test_date_range_conflict():
    with pytest.raises(ConfigError):
        cli._date_range(cli.build_parser().parse_args(["2024-01-01", "--days", "2"]))
    with pytest.raises(ConfigError):
        cli._date_range(cli.build_parser().parse_args(["2024-01-02", "2024-01-01"]))
