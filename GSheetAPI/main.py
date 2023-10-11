from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from create_logger import logger


class GoogleSheetsAPI:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    def __init__(self, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id
        self.token_path = 'GSheetAPI/auth/token.json'
        self.service_creds_path = 'GSheetAPI/auth/servise.json'
        self.service = self._build_service()
        self.sheets = self.service.spreadsheets()

    def _build_service(self):
        """
        Build google api service.
        """
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_creds_path, scopes=self.SCOPES
            )
        except Exception as e:
            logger.error(f"Failed to create service account credentials.")
            logger.error(f"Error: {e}")
            return
        return build('sheets', 'v4', credentials=credentials)

    def insert_data(self, data: list,
                    last_row: int,
                    start_column_literal: str,
                    end_column_literal: str,
                    list_name: str = 'Лист1',
                    start_row: int = 2
                    ) -> bool:
        """
        Insert data into row.
        """
        list_range = f'{list_name}!{start_column_literal}{start_row}:{end_column_literal}{last_row}'
        value_input_option = 'USER_ENTERED'
        request_body = {
            'range': list_range,
            'values': [data],
        }
        try:
            self.sheets.values().update(spreadsheetId=self.spreadsheet_id, range=list_range, body=request_body,
                                        valueInputOption=value_input_option).execute()
            return True
        except HttpError as ex:
            logger.error(f'Fail gsheets_api on insert_data')
            logger.error(f'Error: {ex}')
            return

    def insert_data_into_last_row(self, data: list,
                                  start_column_literal: str,
                                  end_column_literal: str,
                                  list_name: str = 'Лист1') -> bool:
        """
        Insert data in last row in table.
        """
        last_row = self.find_last_empty_row_number('A')
        list_range = f'{list_name}!{start_column_literal}{last_row}:{end_column_literal}{last_row}'
        value_input_option = 'USER_ENTERED'
        request_body = {
            'range': list_range,
            'values': [data],
        }
        try:
            self.sheets.values().update(spreadsheetId=self.spreadsheet_id, range=list_range, body=request_body,
                                        valueInputOption=value_input_option).execute()
            return True
        except HttpError as ex:
            logger.error(f'Fail gsheets_api on insert_data_into_last_row')
            logger.error(f'Error: {ex}')
            return

    def read_data(self, start_column: str, start_row: int, end_column: str, end_row: int):
        """
        Read data from inserted range.
        """
        list_range = f'Лист1!{start_column}{start_row}:{end_column}{end_row}'
        result = self.sheets.values().get(spreadsheetId=self.spreadsheet_id, range=list_range).execute()
        return result

    def find_last_empty_row_number(self, column: str) -> int:
        """
        Finds index of last not filled row with 'A' column.
        """
        list_range = f'Лист1!{column}:{column}'
        result = self.sheets.values().get(spreadsheetId=self.spreadsheet_id, range=list_range).execute()
        values = result.get('values', [])
        return len(values) + 1

    def get_next_ind_of_column(self, column: str) -> int:
        """
        Find the biggest int in column. Returns val + 1.
        """
        last_index = self.find_last_empty_row_number(column)
        result = self.read_data(column, 1, column, last_index)
        try:
            values_list = result['values']
            int_values = [int(item[0]) for item in values_list if item and item[0].isdigit()]
            return max(int_values) + 1 if len(int_values) > 0 else None
        except KeyError as ex:
            logger.error(f'Fail gsheets_api on get_next_ind_of_column')
            logger.error(f'Error: {ex}')
            return
