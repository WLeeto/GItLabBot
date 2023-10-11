import asyncio
import datetime
import logging
import re

from aiogram import Bot, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

from create_bot import dp, bot, db
from create_logger import logger


logging.basicConfig(level=logging.DEBUG)


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("task", "/task <id> <название> <исполнитель> - поставить задачу"),
        types.BotCommand("id", "/id <git_username> - выводит git id пользователя по его нику"),
        types.BotCommand("help", "вывод справки"),
    ])


async def on_startup(_):
    """
    Запуск бота
    """
    asyncio.create_task(set_default_commands(dp))
    db.create_tables()
    logger.info('Бот запущен')


async def on_shutdown(_):
    """
    Завершение работы
    """
    logger.info('Бот отключен')


from handlers import client, admin, other

admin.register_handlers_admin(dp)
client.register_handlers_client(dp)
other.register_handlers_other(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)


