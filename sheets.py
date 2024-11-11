import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from string import ascii_uppercase
from datetime import datetime as dt

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SPREADSHEET_ID = "1xbJEoEsmPjAu2uh3Xgg0funAKlDcrRakEEDyDUxXTww"

google_credentials = os.getenv("GOOGLE_CREDENTIALS")
google_credentials = google_credentials.strip("'")
if google_credentials:
    credentials_info = json.loads(google_credentials)
    creds = service_account.Credentials.from_service_account_info(credentials_info)
else:
    raise ValueError("GOOGLE_CREDENTIALS not set or empty")

scoped_credentials = creds.with_scopes(SCOPES)


def generate_month_columns():
    month_columns = {}
    columns = list(ascii_uppercase[:24])

    start_index = 0
    for i in range(1, 13):
        month_columns[i] = (columns[start_index], columns[start_index + 1])
        start_index += 2
    return month_columns


MONTH_COLUMNS = generate_month_columns()


def get_current_month_columns():
    current_month = dt.now().month
    return MONTH_COLUMNS[current_month]


def get_next_empty_row(service, spreadsheet_id, column):
    range_to_check = f'{column}:{column}'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_to_check
    ).execute()
    values = result.get('values', [])
    next_empty_row = len(values) + 1
    return next_empty_row


def add_expense(data, category):
    try:
        service = build("sheets", "v4", credentials=scoped_credentials)
        month_columns = get_current_month_columns()
        if not month_columns:
            raise ValueError('Нет данных для текущего месяца')

        next_empty_row = get_next_empty_row(
            service,
            SPREADSHEET_ID,
            month_columns[category])

        range_to_add = f'{month_columns[category]}{next_empty_row}'
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_to_add,
            valueInputOption='USER_ENTERED',
            body={'values': [[value] for value in data]}
        ).execute()

    except HttpError as err:
        print(err)
