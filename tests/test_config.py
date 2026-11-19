import pytest

from elicznik import ConfigError, load_credentials, read_env_file


def test_read_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text(
        "# comment\n\nELICZNIK_USERNAME=a@b.pl\nexport ELICZNIK_PASSWORD=\"p#ss = word\"\n"
        "ELICZNIK_SITE=1_2_3  # inline\nEMPTY=\n"
    )
    assert read_env_file(f) == {
        "ELICZNIK_USERNAME": "a@b.pl",
        "ELICZNIK_PASSWORD": "p#ss = word",
        "ELICZNIK_SITE": "1_2_3",
        "EMPTY": "",
    }


def test_read_env_file_rejects_garbage(tmp_path):
    f = tmp_path / ".env"
    f.write_text("not a pair\n")
    with pytest.raises(ConfigError, match=":1:"):
        read_env_file(f)


def test_precedence_flag_env_file(tmp_path):
    f = tmp_path / "creds"
    f.write_text("ELICZNIK_USERNAME=file\nELICZNIK_PASSWORD=filepw\nELICZNIK_SITE=1_1_1\n")
    env = {"ELICZNIK_USERNAME": "env", "ELICZNIK_SITE": "2_2_2"}
    c = load_credentials(env_file=f, environ=env, interactive=False)
    assert (c.username, c.password, c.site) == ("env", "filepw", "2_2_2")
    c = load_credentials(username="flag", site="3_3_3", env_file=f, environ=env, interactive=False)
    assert (c.username, c.site) == ("flag", "3_3_3")


def test_password_not_in_repr():
    c = load_credentials(environ={"ELICZNIK_USERNAME": "u", "ELICZNIK_PASSWORD": "secret"}, interactive=False)
    assert "secret" not in repr(c)


def test_missing_credentials_non_interactive(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ConfigError, match="ELICZNIK_USERNAME and ELICZNIK_PASSWORD"):
        load_credentials(environ={}, interactive=False)


def test_missing_env_file(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_credentials(env_file=tmp_path / "nope", environ={}, interactive=False)


def test_invalid_site():
    with pytest.raises(ConfigError, match="Invalid site"):
        load_credentials(site="abc", environ={"ELICZNIK_USERNAME": "u", "ELICZNIK_PASSWORD": "p"}, interactive=False)
