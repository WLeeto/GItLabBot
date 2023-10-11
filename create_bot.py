from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from os import environ

from GDriveAPI.main import GoogleDriveAPI
from GSheetAPI.main import GoogleSheetsAPI
from Gitlab_API.requests import Gitlab_api
from database.requests import database

storage = MemoryStorage()
# storage = RedisStorage('redis://localhost:6379/0')

token_tg = environ.get("TOKEN_GITLABBOT_BOT")

token_gitlab = environ.get("TOKEN_GITLABBOT_API")

bot = Bot(token=token_tg)

dp = Dispatcher(bot, storage=storage)

gitlab = Gitlab_api(GITLAB_TOKEN=token_gitlab, GITLAB_URL="https://gitlab.teamforce.ru")

spreadsheet_id = '1V50ZNqgb0mGr6X5WN6ojAlcvE7rP92_rcAxaDAxnjc4'  # боевой лист
# spreadsheet_id = '1Hxy6wMW9lN0fqtWjVBnipJEolgJBhzLJDLk9hgs5jxM'  # тестовый лист
google_sheets = GoogleSheetsAPI(spreadsheet_id)
google_drive = GoogleDriveAPI()

db = database()
