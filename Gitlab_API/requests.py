from pprint import pprint

import requests

from create_logger import logger
from datetime import datetime


def get_latest_date(list_of_dates: [datetime]) -> datetime:
    """
    Get the latest date from list of dates.
    """
    latest_date = None
    for date_str in list_of_dates:
        if date_str is not None:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            if not latest_date or latest_date < date:
                latest_date = date
    return latest_date


class Gitlab_api:
    def __init__(self, GITLAB_TOKEN, GITLAB_URL):
        self.token = GITLAB_TOKEN
        self.url = GITLAB_URL

    def get_issure(self, project_id: int, issure_id: int) -> dict:
        """
        Get specific issure.
        estimate = result['time_stats']['time_estimate'] (seconds)
        spend = result['time_stats']['total_time_spent'] (seconds)
        deadline = result['due_date'] (YYYY-MM-DD)
        closed = result['closed_at'] (2023-01-24T05:46:53.777Z)
        """
        url = f"{self.url}/api/v4/projects/{project_id}/issues/{issure_id}"
        headers = {"PRIVATE-TOKEN": self.token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Запрос GET на {url}.\nОшибка: {response.text}")
            return

    def get_all_projects_issures(self, project_id: int):
        """
        Get all issures from specific project.
        """
        url = f"{self.url}/api/v4/projects/{project_id}/issues/"
        headers = {"PRIVATE-TOKEN": self.token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Запрос GET на {url}.\nОшибка: {response.text}")
            return

    def get_issure_deadline(self, project_id: int, issure_id: int) -> datetime:
        """
        Get closed at date if it is or latest closed date from all issures in project.
        """
        closed = self.get_issure(project_id, issure_id).get('closed_at')
        if closed:
            closed = datetime.strptime(closed, '%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            closed = self.get_latest_deadline(project_id)
        return closed

    def get_latest_deadline(self, project_id: int) -> datetime:
        """
        Get latest deadline from specific project.
        """
        all_issures = self.get_all_projects_issures(project_id)
        all_deadlines = [i['due_date'] for i in all_issures]
        return get_latest_date(all_deadlines)

    def get_latest_closed_at(self, project_id: int) -> datetime:
        """
        Get latests close issure date.
        """
        all_issures = self.get_all_projects_issures(project_id)
        all_closed_at = [i['closed_at'] for i in all_issures]
        return get_latest_date(all_closed_at)

    def get_project_id_by_name(self, project_name: str, namespace: str) -> str:
        """
        project_name is a pro
        """
        url = f"{self.url}/api/v4/projects?search={project_name}"
        headers = {"PRIVATE-TOKEN": self.token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            projects = response.json()
            if len(projects) == 1:
                return projects[0]["id"]
            elif len(projects) > 0:
                for project in projects:
                    if project['name_with_namespace'].lower() == f'{namespace.lower()} / {project_name.lower()}':
                        return project["id"]
            else:
                logger.error(f"Проект {project_name} не найден в GitLab.")
                return False
        else:
            logger.error("Ошибка при выполнении запроса API GitLab.")
            return False

    def get_project(self, project_id: str) -> str:
        url = f"{self.url}/api/v4/projects/{project_id}"
        headers = {"PRIVATE-TOKEN": self.token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except KeyError:
                logger.error(f"Ошибка при поиске id")
                return False
        else:
            logger.error(f"Проект {project_id} не найден в GitLab.")
            return False

    def get_projects_group_id(self, project_id: str) -> str:
        url = f"{self.url}/api/v4/projects/{project_id}"
        headers = {"PRIVATE-TOKEN": self.token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                result = response.json()["namespace"]["id"]
                return result
            except KeyError:
                logger.error(f"Ошибка при поиске id")
                return False
        else:
            logger.error(f"Проект {project_id} не найден в GitLab.")
            return False

    def add_issure(self, project_id: int, issue_title: str, issue_description: str, assignee_ids: list) -> dict or bool:
        """
        :return:
        """
        url = f"{self.url}/api/v4/projects/{project_id}/issues"
        headers = {"PRIVATE-TOKEN": self.token}
        group_id = self.get_projects_group_id(project_id)
        milestone_list = self.get_last_milestone_of_group_id(group_id)
        milestone = self._get_current_milestone(milestone_list)
        data = {
            "title": issue_title,
            "description": issue_description,
            "assignee_ids": assignee_ids,
            'milestone_id': milestone.get('id'),
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 201:
            logger.info(f"Новый issue {issue_title} был успешно создан в GitLab.")
            logger.info(f"Vars: group_id:{group_id} milestone_id:{milestone.get('id')} data:{data}")
            return response.json()
        else:
            logger.error("Ошибка при создании issue в GitLab.")
            logger.error(response.json())
            return False

    def add_issure_with_image(self, project_id: int, issue_title: str, issue_description: str,
                              assignee_ids: list, image_path: str, image_name: str) -> dict or bool:
        url = f"{self.url}/api/v4/projects/{project_id}/issues"
        headers = {"PRIVATE-TOKEN": self.token}
        group_id = self.get_projects_group_id(project_id)
        milestone_list = self.get_last_milestone_of_group_id(group_id)
        milestone = self._get_current_milestone(milestone_list)

        image_url = self._upload_image(project_id, image_path, image_name)

        data = {
            "title": issue_title,
            "description": f"{issue_description}\n\n![{image_name}]({image_url})",
            "assignee_ids": assignee_ids,
            'milestone_id': milestone.get('id'),
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 201:
            logger.info(f"Новый issue {issue_title} был успешно создан в GitLab.")
            logger.info(f"Vars: group_id:{group_id} milestone_id:{milestone.get('id')} data:{data}")
            return response.json()
        else:
            logger.error("Ошибка при создании issue в GitLab.")
            logger.error(response.json())
            return False

    def get_user_id_by_nickname(self, nickname: str) -> int or False:
        url = f"{self.url}/api/v4/users"
        headers = {
            "PRIVATE-TOKEN": self.token
        }
        params = {
            "username": nickname
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            user_data = response.json()
            if len(user_data) == 1:
                user_id = user_data[0]["id"]
                return user_id
            elif len(user_data) > 1:
                logger.info(f"Найдено несколько пользователей с ником {params['username']}")
                return False
            else:
                logger.warning(f"Не найдено пользователей с ником {params['username']}")
                return False
        else:
            logger.error(f"Ошибка при выполнении запроса: {response.status_code} - {response.text}")
            return False

    def _get_current_milestone(self, milestone_list: list) -> dict:
        """
        Get latest milestone but not the one witch not started.
        """
        for milestone in milestone_list:
            start = milestone['start_date']
            start_date = datetime.strptime(start, '%Y-%m-%d')
            now = datetime.now()
            if now > start_date:
                return milestone

    def get_last_milestone_of_group_id(self, group_id: int) -> list or False:
        url = f"{self.url}/api/v4/groups/{group_id}/milestones"
        headers = {"PRIVATE-TOKEN": self.token}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            result = response.json()
            if result:
                return result
            else:
                logger.warning(f"У группы {group_id} нет майлстоунов")
                return False
        else:
            logger.error('Ошибка при получении списка майлстоунов.')
            logger.error(response.json())
            return False

    def _upload_image(self, project_id: int, image_path: str, filename: str) -> str or False:
        """
        Возвращает ссылку на загруженный фаил
        """
        url = f"{self.url}/api/v4/projects/{project_id}/uploads"
        headers = {"PRIVATE-TOKEN": self.token}
        with open(image_path, "rb") as image_file:
            data = {
                "file": image_file,
                "filename": filename
            }
            response = requests.post(url, headers=headers, files=data)
        if response.status_code == 201:
            return response.json()["url"]
        else:
            logger.error('Ошибка при получении URL для загрузки файла.')
            logger.error(response.text)
            return False

    def edit_issure_title(self, new_title: str, project_id: int, issure_id: int) -> dict or bool:
        url = f"{self.url}/api/v4/projects/{project_id}/issues/{issure_id}"
        headers = {"PRIVATE-TOKEN": self.token}
        data = {
            "title": new_title,
        }
        response = requests.put(url, headers=headers, data=data)
        if response.status_code == 200:
            logger.info(f"Issure {issure_id} было отредактировано, новое название: {new_title}.")
            return response.json()
        else:
            logger.error("Ошибка при редактировании issue в GitLab.")
            logger.error(response.json())
            return False

    def edit_issure_description(self, new_description: str, project_id: int, issure_id: int) -> dict or bool:
        url = f"{self.url}/api/v4/projects/{project_id}/issues/{issure_id}"
        headers = {"PRIVATE-TOKEN": self.token}
        data = {
            "description": new_description,
        }
        response = requests.put(url, headers=headers, data=data)
        if response.status_code == 200:
            expression = new_description.replace('\n', '')
            logger.info(f"Issure {issure_id} было отредактировано, новое описание: {expression}.")
            return response.json()
        else:
            logger.error("Ошибка при редактировании issue в GitLab.")
            logger.error(response.json())
            return False

