from aiogram import Dispatcher, types
from create_bot import gitlab, db, google_sheets, bot, dp, google_drive
from create_logger import logger
from dicts.messages import message_dict
from keyboards.update_keyboard import update_keyboard

from utils.common import get_photo_path, get_task_text, \
    get_task_name, try_create_issure, delete_temp_file, check_vars_and_send_result, get_variables_with_validations, \
    update_record, get_changes_log_txt, get_video_path


async def help_message(msg: types.Message):
    await msg.answer(message_dict["help_message"], parse_mode=types.ParseMode.HTML)


async def all_users(msg: types.Message):
    text = db.all_users()
    await msg.answer(f"Всего пользователей {len(text)}")


async def test(msg: types.Message):
    await msg.answer("Бот GITLABBOT работает")


# @dp.message_handler()
# async def log(msg: types.Message):
#     temp = {"message_id": 259,
#             "from": {"id": 5148438149,
#                      "is_bot": False,
#                      "first_name": "Oleg",
#                      "last_name": "Mar4",
#                      "username": "WLeeto",
#                      "language_code": "ru"},
#             "chat": {"id": 5148438149,
#                      "first_name": "Oleg",
#                      "last_name": "Mar4",
#                      "username": "WLeeto",
#                      "type": "private"},
#             "date": 1696241534,
#             "reply_to_message": {"message_id": 258,
#                                  "from": {"id": 5148438149,
#                                           "is_bot": False,
#                                           "first_name": "Oleg",
#                                           "last_name": "Mar4",
#                                           "username": "WLeeto",
#                                           "language_code": "ru"},
#                                  "chat": {"id": 5148438149,
#                                           "first_name": "Oleg",
#                                           "last_name": "Mar4",
#                                           "username": "WLeeto",
#                                           "type": "private"},
#                                  "date": 1696241375,
#                                  "animation": {"file_name": "video_2023-09-29_16-05-31.mp4",
#                                                "mime_type": "video/mp4",
#                                                "duration": 5,
#                                                "width": 520,
#                                                "height": 372,
#                                                "thumbnail": {"file_id": "AAMCAgADGQEAAgECZRpsr7LXTiJLQUwwJH2NZS6LU5cAAp07AAJ5ONFIUneUh37gGLYBAAdtAAMwBA",
#                                                              "file_unique_id": "AQADnTsAAnk40Uhy",
#                                                              "file_size": 20843,
#                                                              "width": 320,
#                                                              "height": 229},
#                                                "thumb": {"file_id": "AAMCAgADGQEAAgECZRpsr7LXTiJLQUwwJH2NZS6LU5cAAp07AAJ5ONFIUneUh37gGLYBAAdtAAMwBA",
#                                                          "file_unique_id": "AQADnTsAAnk40Uhy",
#                                                          "file_size": 20843,
#                                                          "width": 320,
#                                                          "height": 229},
#                                                "file_id": "CgACAgIAAxkBAAIBAmUabK-y104iS0FMMCR9jWUui1OXAAKdOwACeTjRSFJ3lId-4Bi2MAQ",
#                                                "file_unique_id": "AgADnTsAAnk40Ug",
#                                                "file_size": 354477},
#                                  "document": {"file_name": "video_2023-09-29_16-05-31.mp4",
#                                               "mime_type": "video/mp4",
#                                               "thumbnail": {"file_id": "AAMCAgADGQEAAgECZRpsr7LXTiJLQUwwJH2NZS6LU5cAAp07AAJ5ONFIUneUh37gGLYBAAdtAAMwBA",
#                                                             "file_unique_id": "AQADnTsAAnk40Uhy",
#                                                             "file_size": 20843,
#                                                             "width": 320,
#                                                             "height": 229},
#                                               "thumb": {"file_id": "AAMCAgADGQEAAgECZRpsr7LXTiJLQUwwJH2NZS6LU5cAAp07AAJ5ONFIUneUh37gGLYBAAdtAAMwBA",
#                                                         "file_unique_id": "AQADnTsAAnk40Uhy",
#                                                         "file_size": 20843,
#                                                         "width": 320,
#                                                         "height": 229},
#                                               "file_id": "CgACAgIAAxkBAAIBAmUabK-y104iS0FMMCR9jWUui1OXAAKdOwACeTjRSFJ3lId-4Bi2MAQ",
#                                               "file_unique_id": "AgADnTsAAnk40Ug",
#                                               "file_size": 354477}},
#             "text": "реплай"}
#
#     logger.info(msg)


async def create_gitlab_task(msg: types.Message):
    if msg.reply_to_message:
        project_id_pattern = r"/task (\d+)"
        task_name_pattern = r"/task\s+(\d+)?(.*)(\s+@)"
        users_pattern = r"@[\S]+"
        gitlab_vars = await get_variables_with_validations(msg, users_pattern, project_id_pattern)
        if not gitlab_vars:
            return
        photo_path = await get_photo_path(msg)
        video_path, video_file_id = await get_video_path(msg)

        task_text = await get_task_text(msg, photo_path)
        task_name = await get_task_name(msg, task_name_pattern, task_text)
        temp_message = await msg.answer("Ставлю задачу ...")
        issure, file = await try_create_issure(msg, photo_path, gitlab_vars['project_id'], task_name, task_text,
                                         gitlab_vars['user_dict'], video_path, video_file_id)
        await delete_temp_file(photo_path)
        await delete_temp_file(video_path)
        url = file['webViewLink'] if file else None
        await check_vars_and_send_result(msg, temp_message, issure, gitlab_vars['users'], task_name, task_text, url)


async def update(msg: types.Message):
    text = msg.text.split(' ')
    if len(text) == 2:
        try:
            task = int(text[1])
        except ValueError:
            await msg.answer('Неверный номер задачи.')
            return
        changes = {}
        end_row = google_sheets.find_last_empty_row_number('A')
        total_temp_data = google_sheets.read_data('A', 1, 'AC', end_row)['values']
        for data in total_temp_data:
            if data[1] == str(task):
                row = total_temp_data.index(data) + 1
                changes.setdefault(row, await update_record(row, data, force=True))
        if changes:
            await msg.answer(f'Данные обновлены.')
            await get_changes_log_txt(changes, msg.from_id)
        else:
            await msg.answer('Нет изменений.')

    elif msg.from_id in [5148438149, 183417405] and len(text) == 1:
        await bot.send_message(msg.from_id, 'Эта операция пройдет по всем строкам таблицы и заполнит пустые поля '
                                            'согласно скрипту. Время выполнения 2-5 минут. Желательно чтобы в это '
                                            'время в таблицу не вносились изменения. Продолжить ?',
                               reply_markup=update_keyboard)


async def update_procceed(cbq: types.CallbackQuery):
    await cbq.message.edit_text('Выполняю ...')
    if cbq.data.split(' ')[1] == 'yes':
        end_row = google_sheets.find_last_empty_row_number('A')
        start_row = 2
        total_temp_data = google_sheets.read_data('A', start_row, 'AC', end_row)['values']

        changes = {}
        for temp_data in total_temp_data:
            changes.setdefault(start_row, await update_record(start_row, temp_data))
            start_row += 1

        await cbq.message.edit_text('Данные обновлены.')
        await get_changes_log_txt(changes, cbq.from_user.id)
    else:
        await cbq.message.edit_text('Отменено.')


async def get_user_git_id(msg: types.Message):
    user_name = msg.text.replace("/id ", "")
    user_git_id = gitlab.get_user_id_by_nickname(user_name)
    text = f"У пользователя <code>{user_name}</code> id <code>{user_git_id}</code>"
    await msg.answer(text, parse_mode=types.ParseMode.HTML)


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(all_users, commands="all")
    dp.register_message_handler(help_message, commands="help")
    dp.register_message_handler(test, commands="test")
    dp.register_message_handler(create_gitlab_task, commands="task")
    dp.register_message_handler(get_user_git_id, commands="id")
    dp.register_message_handler(update, commands="update")
    dp.register_callback_query_handler(update_procceed, lambda c: c.data.startswith('update_answer'))
