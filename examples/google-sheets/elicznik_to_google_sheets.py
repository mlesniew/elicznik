#!/usr/bin/env python3
"""Download eLicznik readings and write them to a Google Sheets document.

This script will download readings from the Tauron eLicznik website and
upload them to a defined Google Sheets spreadsheet.  The script can be
run periodically to update the spreadsheet with new readings without
overwriting the old ones.

The Google Sheets ID and the Tauron eLicznik login and password can be
provided on the command line or by setting the ELICZNIK_GOOGLE_SHEETS_ID,
ELICZNIK_LOGIN and ELICZNIK_PASSWORD environment variables respectively.
Values passed in the command line take precedence over the environment
variables if both are present.

A Google service account needs to be set up as described at
https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account
and a service_account.json file must be present and readable.

Note that the Google Sheet ID is the identifier of the Spreadsheet, as it
appears in the URL when opened in the browser.  It is not the full URL nor
the Google Sheet title.

The spreadsheet must be shared with the service account user.  Please refer
to gspread library documentation for more information.
"""

import argparse
import datetime
import os

import elicznik
import gspread


def format_worksheet(worksheet):
    worksheet.batch_format(
        [
            {
                "range": f"A1:Z1",
                "format": {
                    "borders": {
                        "bottom": {
                            "style": "SOLID_MEDIUM",
                        }
                    },
                    "horizontalAlignment": "CENTER",
                    "textFormat": {
                        "bold": True,
                    },
                },
            },
            {
                "range": f"A2:A{worksheet.row_count}",
                "format": {
                    "borders": {
                        "right": {
                            "style": "SOLID_MEDIUM",
                        }
                    },
                    "numberFormat": {
                        "type": "DATE",
                        "pattern": "yyy-MM-dd",
                    },
                    "textFormat": {
                        "bold": True,
                    },
                },
            },
            {
                "range": f"B2:Z{worksheet.row_count}",
                "format": {
                    "numberFormat": {
                        "type": "NUMBER",
                        "pattern": "0.00",
                    },
                },
            },
            {
                "range": f"Z2:{worksheet.row_count}",
                "format": {
                    "numberFormat": {
                        "type": "NUMBER",
                        "pattern": "0.0",
                    },
                    "borders": {
                        "left": {
                            "style": "SOLID",
                        }
                    },
                },
            },
        ]
    )
    worksheet.freeze(1, 1)


def get_or_create_worksheet(spreadsheet, title):
    worksheets = [
        ws for ws in spreadsheet.worksheets() if ws.title.lower() == title.lower()
    ]
    if worksheets:
        print(f"Found '{title}' spreadsheet...")
        return worksheets[0]
    print(f"Creating new '{title}' spreadsheet...")
    worksheet = spreadsheet.add_worksheet(title, rows=1000, cols=26)
    HEADERS = ["Date"] + list(range(24)) + ["Σ"]
    worksheet.append_row(HEADERS)
    format_worksheet(worksheet)
    return worksheet


def add_or_update_row(worksheet, date, values):
    date_string = date.isoformat()
    values = [date_string] + [values.get(i) for i in range(24)]
    cell = worksheet.find(date_string, in_column=1)
    if not cell:
        cell = worksheet.append_row(values, value_input_option="USER_ENTERED")
        cell = worksheet.find(date_string, in_column=1)
    else:
        worksheet.batch_update(
            [
                {
                    "range": f"A{cell.row}:Y{cell.row}",
                    "values": [values],
                }
            ],
            value_input_option="USER_ENTERED",
        )
    worksheet.batch_update(
        [
            {
                "range": f"Z{cell.row}:Z{cell.row}",
                "values": [[f"=SUM(B{cell.row}:Y{cell.row})"]],
            }
        ],
        value_input_option="USER_ENTERED",
    )


def date_range(start, end, step=datetime.timedelta(days=1)):
    date = start
    while date <= end:
        yield date
        date += step


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--login", help="Tauron login", default=os.getenv("ELICZNIK_LOGIN")
    )
    parser.add_argument(
        "--password", help="Tauron password", default=os.getenv("ELICZNIK_PASSWORD")
    )
    parser.add_argument(
        "sheet", help="Google Sheet ID", default=os.getenv("ELICZNIK_GOOGLE_SHEETS_ID")
    )
    parser.add_argument(
        "--days", default=5, type=int, help="Number of past days to retrieve"
    )
    args = parser.parse_args()

    if not args.login or not args.password:
        raise SystemExit("No login or password provided.")

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=args.days)

    print(f"Downloading eLicznik data for {start_date} to {end_date}...")
    with elicznik.ELicznik(args.login, args.password) as licznik:
        elicznik_readings = [
            (dt - datetime.timedelta(hours=1), c, p)
            for dt, c, p in licznik.get_readings(start_date, end_date)
        ]
    print(f"Got {len(elicznik_readings)} data points.")

    data = {
        "eLicznik Produkcja": {dt: p for dt, c, p in elicznik_readings},
        "eLicznik Konsumpcja": {dt: c for dt, c, p in elicznik_readings},
    }

    print("Updating spreadsheet...")
    gc = gspread.service_account()
    spreadsheet = gc.open_by_key(args.sheet)

    for sheet_title, sheet_data in data.items():
        worksheet = get_or_create_worksheet(spreadsheet, sheet_title)

        print(f"Updating worksheet '{sheet_title}'...")
        for date in date_range(start_date, end_date):
            values = {dt.hour: v for dt, v in sheet_data.items() if dt.date() == date}
            if not values:
                print(f"No values for {date}, skipping...")
                continue
            add_or_update_row(worksheet, date, values)
            print(f"Worksheet '{sheet_title}' updated with values for {date}.")

        format_worksheet(worksheet)
        print(f"Worksheet '{sheet_title}' update complete.")

    print("Spreadsheet update complete.")


if __name__ == "__main__":
    main()
