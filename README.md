# Tauron eLicznik

Python client and command line tool that downloads hourly energy readings from
[Tauron eLicznik](https://elicznik.tauron-dystrybucja.pl/): consumption, production and
their balanced (net) values, in kWh.

Output is designed to be consumed by other programs: JSON Lines by default, UTC timestamps,
data on stdout, logs on stderr, and distinct exit codes.

## Installation

```
pip install elicznik
```

Requires Python 3.10+.

## Credentials

Copy [`.env.example`](.env.example) to `.env` and fill it in:

```
ELICZNIK_USERNAME=freddy@example.com
ELICZNIK_PASSWORD=change-me
ELICZNIK_SITE=
```

`ELICZNIK_SITE` (metering point, format `123_456_789`) is only needed for accounts with
several meters.

Values are resolved in this order: command line flags (`--username`, `--site`), environment
variables, the `.env` file (`./.env`, or `--env-file PATH`), then an interactive prompt when
running in a terminal. The password is never accepted as a command line argument.

## Command line

```
elicznik [START] [END] [--days N] [-f jsonl|json|csv|table] [-o FILE]
         [-u USERNAME] [--site SITE] [--env-file PATH] [-v | -q]
```

| Argument | Meaning |
| --- | --- |
| `START` `END` | Local days (`YYYY-MM-DD`), inclusive. Default: yesterday. |
| `--days N` | The last N days, ending yesterday. |
| `-f`, `--format` | `jsonl` (default), `json`, `csv` or `table`. |
| `-o`, `--output` | Write to a file atomically instead of stdout. |

```
$ elicznik 2022-07-20
{"start": "2022-07-19T22:00:00Z", "end": "2022-07-19T23:00:00Z", "local_start": "2022-07-20T00:00:00+02:00", "consumption": 0.133, "production": 0.0, "net_consumption": 0.133, "net_production": 0.0}
...

$ elicznik --days 7 | jq -s 'map(.consumption // 0) | add'
42.517

$ elicznik 2022-07-20 -f table
local time             consumption  production  net cons.  net prod.
---------------------  -----------  ----------  ---------  ---------
2022-07-20 00:00 CEST        0.133       0.000      0.133      0.000
...
```

### Output

Every format uses the same fields:

| Field | Description |
| --- | --- |
| `start`, `end` | Hour boundaries, ISO 8601 UTC. |
| `local_start` | Hour start in `Europe/Warsaw`, with offset. |
| `consumption` | Energy taken from the grid (kWh). |
| `production` | Energy fed into the grid (kWh). |
| `net_consumption` | Taken after hourly balancing (kWh). |
| `net_production` | Fed in after hourly balancing (kWh). |

Values not yet published by Tauron are `null` (empty in CSV). DST days have 23 or 25 hourly records.
`--format json` wraps the records in `{"site", "from", "to", "unit", "timezone", "readings"}`.

### Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 1 | Unexpected error |
| 2 | Invalid arguments or missing credentials |
| 3 | Invalid username or password |
| 4 | Rate limited or account temporarily blocked |
| 5 | Unexpected response from Tauron |

## Python API

```python
from datetime import date
import elicznik

credentials = elicznik.load_credentials()  # environment / .env
with elicznik.Client.from_credentials(credentials) as client:
    for r in client.readings(date(2022, 7, 1), date(2022, 7, 31)):
        print(r.local_start, r.consumption, r.production)
```

`Client("user", "password", site=None)` can also be constructed directly. Readings are frozen
dataclasses with a timezone-aware UTC `start`; `Reading.to_dict()` returns the output schema.
Errors derive from `elicznik.ElicznikError` (`AuthError`, `RateLimitError`, `ResponseError`,
`ConfigError`).

See [`examples/google-sheets`](examples/google-sheets) for a script that syncs readings to a
spreadsheet.

## Upgrading from 2.x

Version 3 is a rewrite. `ELicznik`, `ELicznikCSV` and `ELicznikChart` are replaced by `Client`,
readings by the `Reading` dataclass with UTC timestamps, and the CLI defaults to JSON Lines
(use `-f table` for the old view). The `--api` option is gone; only the CSV export is used.

## Related projects

- [tauron-elicznik-scraper](https://github.com/MichalZaniewicz/tauron-elicznik-scraper) by Michał Zaniewicz, which this project was originally based on.
- [Tauron AMIplus sensor](https://github.com/PiotrMachowski/Home-Assistant-custom-components-Tauron-AMIplus): a Home Assistant integration.
- [home-assistant-tauron-elicznik](https://github.com/UrbanskiDawid/home-assistant-tauron-elicznik): a minimal Home Assistant integration for hourly consumption.

## License

[MIT](LICENSE). Unofficial; not affiliated with TAURON.
