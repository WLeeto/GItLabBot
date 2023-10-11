from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

from create_logger import logger


class GoogleDriveAPI:
    def __init__(self):
        self.sevise_account_creds = 'GDriveAPI/auth/servise.json'
        FOLDER_ID = '1nOCrkoSdzqqpWK_hq77l8nX2OmHQYMbl'
        self.credentials = service_account.Credentials.from_service_account_file(
            self.sevise_account_creds, scopes=['https://www.googleapis.com/auth/drive'])
        self.drive_service = self._build_service()

    def _build_service(self):
        return build('drive', 'v3', credentials=self.credentials)

    def load_file(self, file_name: str, file_path: str) -> str:
        """
        Loads file to cloud.
        :param file_name: filename on cloud
        :param file_path: path to uploaded file.
        :return: id of uploaded file
        """
        media = MediaFileUpload(file_path,
                                mimetype='video/mp4',
                                resumable=True)
        file_metadata = {
            'name': file_name,
            'mimeType': 'video/mp4',
        }
        try:
            file = self.drive_service.files().create(body=file_metadata,
                                                media_body=media,
                                                fields='id, webViewLink').execute()
            return file
        except Exception as ex:
            logger.error(f'Cant load file {file_path}. Error:\n{ex}')

    def set_permissions(self, file_id) -> bool:
        permissions = {
            'role': 'reader',
            'type': 'anyone'
        }
        try:
            self.drive_service.permissions().create(fileId=file_id, body=permissions).execute()
            return True
        except Exception as ex:
            logger.error(f'Cant set permissions to file {file_id}.Error:\n{ex}')