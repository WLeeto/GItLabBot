import os
import re
from datetime import date

from aiogram import types
from aiogram.utils.exceptions import BadRequest

from Gitlab_API.requests import get_latest_date
from create_bot import google_sheets, db, gitlab, bot, google_drive
from create_logger import logger


async def add_google_sheet_data(message: types.Message, task_name: str, task_text: str, issure: dict,
                                url: str = None) -> None:
    answer = await message.answer('Пытаюсь создать запись в gsheets ...')
    re_pattern = r'#blog (\d+)'
    match = re.search(re_pattern, message.text)

    if match is not None:
        task_number = match.group(1)
        end_row = google_sheets.find_last_empty_row_number('A')
        total_temp_data = google_sheets.read_data('A', 2, 'AC', end_row)['values']
        row = 2
        result = None
        for data in total_temp_data:
            if len(data) >= 18:
                if str(data[1]) == str(task_number):
                    data[17] += f'\n{issure["web_url"]}'
                    result = google_sheets.insert_data(data=[data[17]],
                                                       start_column_literal='R',
                                                       start_row=row,
                                                       end_column_literal='R',
                                                       last_row=row)
                    break
            row += 1

        if result:
            new_description = f'{issure["description"]}\n\n#blog {task_number}'
            gitlab.edit_issure_description(new_description, issure['project_id'], issure['iid'])
            await answer.edit_text(f'Ссылка добавлена в задачу {task_number}, строка {row}.')
        elif not result and row >= len(total_temp_data):
            await answer.edit_text(f'Не удалось найти запись {task_number}.')
        else:
            await answer.edit_text("Не удалось создать запись")
    else:
        a = google_sheets.get_next_ind_of_column('A')
        b = google_sheets.get_next_ind_of_column('B')
        c = task_text
        d = task_name
        e = date.today().strftime('%d.%m.%Y')
        r = issure['web_url']
        i = await get_project_name_by_id(issure['project_id'])
        j = 'Принято в работу'
        q = url

        data_to_insert = [a, b, c, d, e, '', '', '', i, j, '', '', '', '', '', '', q, r]
        result = google_sheets.insert_data_into_last_row(data_to_insert, 'A', 'R')
        if result:
            await answer.edit_text(f'Создана новая запись\n№ п/п <code>{a}</code>\n№ задачи <code>{b}</code>',
                                   parse_mode=types.ParseMode.HTML)
            new_title = f'{issure["description"]}\n\n#blog {b}'
            gitlab.edit_issure_description(new_title, issure['project_id'], issure['iid'])
        else:
            await answer.edit_text('Не удалось создать запись')


async def get_project_name_by_id(project_id: int) -> str:
    """
    Get project name by its id.
    """
    project = gitlab.get_project(project_id)
    if project:
        return project['name']
    return ' '


async def get_photo_path(msg: types.Message) -> str:
    """
    Get path to downloaded photo or None if no photo.
    """
    photo_path = f"{os.getcwd()}/temp/{msg.text[0:5]}"
    if msg.reply_to_message.photo:
        await msg.reply_to_message.photo[-1].download(destination_file=photo_path)
        return photo_path
    elif msg.reply_to_message.document and 'image' in msg.reply_to_message.document.mime_type:
        await msg.reply_to_message.document.download(destination_file=photo_path)
        return photo_path
    else:
        return


async def get_video_path(msg: types.Message) -> str:
    if msg.reply_to_message.document and "video" in msg.reply_to_message.document.mime_type:
        video_file_name, file_id = await get_params_from_repl_msg(msg, 'doc')
        return video_file_name, file_id
    elif msg.reply_to_message.video:
        video_file_name, file_id = await get_params_from_repl_msg(msg, 'video')
        return video_file_name, file_id
    else:
        return None, None


async def get_params_from_repl_msg(msg: types.message, media_type: str):
    if media_type == 'doc':
        file_id = msg.reply_to_message.document.file_id
    elif media_type == 'video':
        file_id = msg.reply_to_message.video.file_id
    else:
        return
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    video_data = await bot.download_file(file_path)

    video_file_name = f"{os.getcwd()}/temp/{file_id}.mp4"

    with open(video_file_name, 'wb') as video_file:
        video_file.write(video_data.read())

    return video_file_name, file_id


async def find_users(users: list) -> dict:
    """
    Try to find user's id's from msg.
    """
    returned_dict = {
        'users_ids': [],
        'not_found_users': []
    }
    for i in users:
        user_id = db.get_user_by_tg_nickname(i)
        if user_id:
            returned_dict['users_ids'].append(user_id.git_id)
        else:
            returned_dict['not_found_users'].append(str(i))
    return returned_dict


async def find_project_id(msg: types.Message, project_id_pattern: str, users: list) -> int:
    """
    Try to get project id from msg, or use default if can't.
    """
    try:
        return re.search(project_id_pattern, msg.text).group(1)
    except (IndexError, AttributeError):
        user_default_project = db.get_user_by_tg_nickname(users[0]).default_project_id
        if user_default_project:
            return user_default_project
        else:
            return


async def get_task_text(msg: types.Message, photo_path: str) -> str:
    """
    Try go get task text or use default.
    """
    default_task_text = "Пользователь не создал описание, предполагается что прикрепленное фото все объясняет"
    if not photo_path:
        if msg.reply_to_message.text:
            return msg.reply_to_message.text
        else:
            return "Нет описания задачи"
    else:
        caption_text = msg.reply_to_message.caption
        return caption_text if caption_text else default_task_text


async def get_task_name(msg: types.Message, task_name_pattern: str, task_text: str) -> str:
    """
    Try to get task name, or get default.
    """
    try:
        task_name = re.match(task_name_pattern, msg.text).group(2)
        return task_name if task_name else task_text[:25]
    except (IndexError, AttributeError):
        return task_text if task_text and len(task_text) <= 100 else task_text[0:100] + "..."


async def try_create_issure(msg: types.Message, photo_path: str, project_id: int, task_name: str, task_text: str,
                            user_dict: dict, video_path: str = None, video_file_id: str = None) -> dict:
    """
    Try to create issure, return False if can't.
    """
    res = None
    file = None
    if not photo_path and not video_path:
        res = gitlab.add_issure(project_id=project_id,
                                issue_title=task_name,
                                issue_description=msg.reply_to_message.text,
                                assignee_ids=user_dict['users_ids']
                                )
    elif video_path:
        file = google_drive.load_file(file_name=video_file_id, file_path=video_path)
        if file:
            temp = google_drive.set_permissions(file['id'])
            if temp:
                if msg.reply_to_message.caption:
                    text = msg.reply_to_message.caption
                else:
                    text = ''
                description = text + '\n' + file['webViewLink']
                res = gitlab.add_issure(project_id=project_id,
                                        issue_title=task_name,
                                        issue_description=description,
                                        assignee_ids=user_dict['users_ids']
                                        )
    else:
        res = gitlab.add_issure_with_image(project_id=project_id,
                                           issue_title=task_name,
                                           issue_description=task_text,
                                           assignee_ids=user_dict['users_ids'],
                                           image_path=photo_path,
                                           image_name=msg.text[0:5]
                                           )
    logger.info(res)
    return res, file


async def delete_temp_file(path: str) -> None:
    """
    Delete temp photo file if exists.
    """
    if not path:
        return
    os.remove(path)


async def validate_variables() -> None:
    """

    """
    pass


async def check_vars_and_send_result(msg: types.Message, temp_message: types.Message, issure: dict, users: list, task_name: str,
                                     task_text: str, url: str) -> None:
    """
    Send final message for /task command.
    """
    if issure:
        await temp_message.edit_text(f"Новая <a href='{issure['web_url']}'>задача</a> {users[0]} {task_name}",
                                     parse_mode=types.ParseMode.HTML)
        if '#blog' in msg.text:
            await add_google_sheet_data(msg, task_text, task_name, issure, url)
        if '#estimate' in msg.text:
            pass



    else:
        await temp_message.edit_text("Ничего не вышло, смотри логи", parse_mode=types.ParseMode.HTML)


async def get_variables_with_validations(msg: types.Message, users_pattern: str, project_id_pattern: str) -> dict:
    """

    """
    returned_dict = {
        'users': re.findall(users_pattern, msg.text),
        'user_dict': None,
        'project_id': None
    }

    if not returned_dict['users']:
        await msg.answer("Не указан список получателей")
        return

    returned_dict['user_dict'] = await find_users(returned_dict['users'])
    if returned_dict['user_dict']['not_found_users']:
        await msg.answer(f"Я не смог найти id следующих пользователей:\n"
                         f"{' ,'.join(returned_dict['user_dict']['not_found_users'])}")
        return

    returned_dict['project_id'] = await find_project_id(msg, project_id_pattern, returned_dict['users'])
    if not returned_dict['project_id']:
        await msg.answer("Не указан id проекта")
        return

    return returned_dict


def get_vars_from_href(href):
    """
    estimate = O , 14
    spend = P , 15
    plan_deadline = L , 11
    fact_ending = M , 12
    work_status = K, 10
    href = R , 17
    """
    project_name = href.split('/')[-4]
    issure_id = href.split('/')[-1]
    namespace = href.split("/")[-5]
    return project_name, issure_id, namespace


def get_git_lab_values(project_id, issure_id) -> dict:
    """
    Get estimate and spent values for issure.
    """
    issure = gitlab.get_issure(project_id, issure_id)
    estimate = issure['time_stats']['time_estimate']
    if estimate is not None:
        estimate = int(estimate / 3600)
    spent = issure['time_stats']['total_time_spent']
    if estimate is not None:
        spent = int(estimate / 3600)
    return {
        'estimate': estimate,
        'spent': spent,
    }


async def get_values_from_hreflist(href_list: list, data: list) -> dict:
    """
    Get dict of values for all hrefs in list.
    """
    issures_dict = {
        'project_name': None,
        'issures_ids': [],
        'estimate': [],
        'spent': [],
        'deadline_plan': [],
        'deadline_fact': [],
    }
    for href in href_list:
        if not href or data[10] == 'Отклонено':
            continue

        project_name, issure_id, namespace = get_vars_from_href(href)
        issures_dict['project_name'] = project_name
        issures_dict['issures_ids'].append(issure_id)
        project_id = gitlab.get_project_id_by_name(project_name, namespace)
        issure = gitlab.get_issure(project_id, issure_id)
        deadline_plan = issure.get('due_date')
        if deadline_plan:
            issures_dict['deadline_plan'].append(deadline_plan)
        deadline_fact = issure.get('closed_at')
        if deadline_fact:
            issures_dict['deadline_fact'].append(deadline_fact)
        estimate = issure['time_stats']['time_estimate']
        if estimate is not None:
            estimate = int(estimate / 3600)
            issures_dict['estimate'].append(estimate)
        spent = issure['time_stats']['total_time_spent']
        if spent is not None:
            spent = int(spent / 3600)
            issures_dict['spent'].append(spent)
    return issures_dict


async def update_record(row: int, data: list, force: bool = False):
    """
    Updates row of values in g-sheets.
    :param row: row to update.
    :param data: list of data to update.
    :param force: force update, update cells even if it has value. (default False)
    :return:
    """
    new_changes = {}
    new_changes.setdefault(row, {})
    logger.warning(f'row:{row} data:{data}')

    try:
        href_cell = data[17]
        if not href_cell:
            return
        href_list = href_cell.split('\n')
    except IndexError:
        return

    issures_dict = await get_values_from_hreflist(href_list, data)

    # estimate. Column 0. Index 14.
    if (not force and not data[14] and issures_dict['estimate']) or (force and issures_dict['estimate']):
        total_estimate = sum(issures_dict['estimate'])
        if total_estimate != 0:
            old_value = data[14]
            data[14] = total_estimate
            logger.warning(f"estimate change to {total_estimate}")
            new_changes[row].setdefault('O', [old_value, data[14]])
    # spend. Column P. Index 15.
    if (not force and not data[15] and issures_dict['spent']) or (force and issures_dict['spent']):
        total_spent = sum(issures_dict['spent'])
        if total_spent != 0:
            old_value = data[14]
            data[15] = total_spent
            logger.warning(f"spent change to {total_spent}")
            new_changes[row].setdefault('P', [old_value, data[15]])
    # plan_deadline. Colunm L. Index 11.
    if (not force and not data[11] and issures_dict['deadline_plan']) or (force and issures_dict['deadline_plan']):
        try:
            oldest_deadline = get_latest_date(issures_dict['deadline_plan']).strftime('%d.%m.%Y')
            old_value = data[11]
            data[11] = oldest_deadline
            logger.warning(f"plan_deadline change to {oldest_deadline}")
            new_changes[row].setdefault('L', [old_value, data[11]])
        except AttributeError:
            pass
    # fact_deadline. Column M. Index 12.
    if (not data[12] and not force) or force \
            and len(issures_dict['deadline_fact']) == len(issures_dict['issures_ids']):
        try:
            oldest_fact = get_latest_date(issures_dict['deadline_fact']).strftime('%d.%m.%Y')
            old_value = data[12]
            data[12] = oldest_fact
            logger.warning(f"deadline_fact change to {oldest_fact}")
            new_changes[row].setdefault('M', [old_value, data[12]])
        except AttributeError:
            pass
    # work_status. Column K. Index 10.
    if data[10] != 'Закрыто' and data[10] != 'Выполнено' \
            and len(issures_dict['deadline_fact']) == len(issures_dict['issures_ids']):
        old_value = data[10]
        data[10] = 'Выполнено'
        logger.warning(f"work_status change to Выполнено")
        new_changes[row].setdefault('K', [old_value, data[10]])

    if not google_sheets.insert_data(data=data,
                                     start_row=row,
                                     last_row=row,
                                     start_column_literal='A',
                                     end_column_literal='AC'):
        logger.error(f'Ошибка на строке {row}')
    return new_changes.get(row)


async def get_changes_log_txt(changes: dict, chat_id: int):
    """

    """
    text = ''
    sub_text = ''
    for row, changes in changes.items():
        if changes:
            for column, data in changes.items():
                sub_text += f'Столбец {column}: {data[0]} -> {data[1]}  '
            text += f'\n<b>Строка:</b>{row}\n  {sub_text}\n'

    with open('changes.txt', 'w', encoding='utf-8') as file:
        file.write(text)

    with open('changes.txt', 'rb') as file:
        try:
            await bot.send_document(chat_id=chat_id, document=file)
        except BadRequest:
            logger.warning('empty file changes.txt wasnt sent.')
    os.remove('changes.txt')
