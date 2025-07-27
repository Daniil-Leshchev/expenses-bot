import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from string import ascii_uppercase
from datetime import datetime as dt

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

google_credentials = os.getenv("GOOGLE_CREDENTIALS")
if google_credentials:
    credentials_info = json.loads(google_credentials)
    creds = service_account.Credentials.from_service_account_info(
        credentials_info)
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


TOTAL_COLUMN = 'D'


def get_monthly_total():
    service = build("sheets", "v4", credentials=scoped_credentials)
    month = dt.now().month
    # строка = месяц + 1 (учитывая заголовок в первой строке)
    row = month + 1
    cell = f'{TOTAL_COLUMN}{row}'
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f'Подсчет!{cell}'
    ).execute()
    values = result.get('values', [])
    total_str = values[0][0] if values and values[0] else None
    try:
        total_val = float(total_str)
    except (TypeError, ValueError):
        total_val = 0.0

    balance_cell = 'N2'
    balance_result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f'Подсчет!{balance_cell}'
    ).execute()
    balance_values = balance_result.get('values', [])
    balance_str = balance_values[0][0] if balance_values and balance_values[0] else None
    try:
        balance_val = float(balance_str)
    except (TypeError, ValueError):
        balance_val = 0.0

    remaining = balance_val - total_val
    return total_val, remaining
