import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from string import ascii_uppercase
from datetime import datetime as dt

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SPREADSHEET_ID = "1xbJEoEsmPjAu2uh3Xgg0funAKlDcrRakEEDyDUxXTww"


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


def get_category_column():
    category = int(input('Введите номер категории: '))
    return category


def get_next_empty_row(service, spreadsheet_id, column):
    range_to_check = f'{column}:{column}'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_to_check
    ).execute()
    values = result.get('values', [])
    next_empty_row = len(values) + 1
    return next_empty_row


def add_expense(spreadsheet_id, data):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("sheets", "v4", credentials=creds)
        month_columns = get_current_month_columns()
        if not month_columns:
            raise ValueError('Нет данных для текущего месяца')

        category = get_category_column()
        next_empty_row = get_next_empty_row(
            service,
            spreadsheet_id,
            month_columns[category])

        range_to_add = f'{month_columns[category]}{next_empty_row}'
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_to_add,
            valueInputOption='USER_ENTERED',
            body={'values': [[value] for value in data]}
        ).execute()

        print('Запись добавлена')

    except HttpError as err:
        print(err)


if __name__ == "__main__":
    add_expense(SPREADSHEET_ID, ['111', '112'])
