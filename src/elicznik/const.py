"""Tauron eLicznik endpoints and constants."""

SERVICE_URL = "https://elicznik.tauron-dystrybucja.pl"
LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"
SELECT_SITE_URL = f"{SERVICE_URL}/ustaw_punkt"
DATA_URL = f"{SERVICE_URL}/energia/do/dane"
BLOCK_PATH = "/blokada"

TIME_ZONE = "Europe/Warsaw"
USER_AGENT = "elicznik (+https://github.com/mlesniew/elicznik)"

ENV_USERNAME = "ELICZNIK_USERNAME"
ENV_PASSWORD = "ELICZNIK_PASSWORD"
ENV_SITE = "ELICZNIK_SITE"
SITE_PATTERN = r"^\d+_\d+_\d+$"

# Prefix of the "Rodzaj" column (lowercased) -> Reading field.
ENERGY_TYPES = {
    "pobór": "consumption",
    "oddanie": "production",
    "pobrana po zbil": "net_consumption",
    "oddana po zbil": "net_production",
}
