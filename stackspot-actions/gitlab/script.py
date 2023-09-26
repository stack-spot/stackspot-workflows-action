import json
import os
from typing import Any

import requests


class GitlabCreateRepoException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class InvalidInputException(GitlabCreateRepoException):
    pass


class GroupNotFound(GitlabCreateRepoException):
    def __init__(self, group_name):
        super().__init__(f"The '{group_name}' group was not found.")


class ProjectAlreadyExistsInTheGroup(GitlabCreateRepoException):
    def __init__(self, group_name, group_id, project_name):
        super().__init__(
            f"The project (repository) '{project_name}' already exists in the group '{group_name}' (group_id={group_id})."
        )


class StkLocalContext:
    """
    An instance of this class represents the STK Local Context
    """
    OUTPUT_FILE_NAME = "stk-local-context.json"

    def __init__(self, json_indent=4):
        self.json_indent = json_indent

    def export_repository_url(self, repository_url):
        """
        Exports Gitlab repository URL to STK local context in the disk
        """
        data = {
            "outputs": {
                "created_repository": repository_url
            }
        }
        with open(self.OUTPUT_FILE_NAME, "w") as file:
            json.dump(data, file, indent=self.json_indent)

    def get_content(self) -> dict:
        """
        Loads STK local context from the disk
        """
        with open(self.OUTPUT_FILE_NAME) as output:
            return json.load(output)

    def clear(self):
        """
        Clears STK local context by deleting the file from the disk
        """
        if os.path.exists(self.OUTPUT_FILE_NAME):
            os.remove(self.OUTPUT_FILE_NAME)


class Runner:
    def __init__(self, metadata, base_url="https://gitlab.com") -> None:
        self.base_url = base_url
        self.group_name = metadata.inputs.get("group_name")
        self.project_name = metadata.inputs.get("project_name")
        self.visibility = metadata.inputs.get("visibility", "private")  # default=private
        self.token = metadata.inputs.get("token")  # injected by the StackSpot Portal
        self._enable_ssl_verify_env = os.getenv("GITLAB_HTTP_SSL_VERIFY_ENABLED", "true")  # default=enabled
        self._enable_logging_env = os.getenv("GITLAB_HTTP_LOGGING_ENABLED", "false")  # default=disabled
        self._request_timeout_env = os.getenv("GITLAB_HTTP_REQUEST_TIMEOUT", "10")  # default=10s
        self.headers = {
            "Private-Token": self.token,
            "Content-Type": "application/json"
        }
        if self.enable_logging:
            self.__enable_logging()

    @property
    def enable_ssl_verify(self) -> bool:
        return (self._enable_ssl_verify_env
                and self._enable_ssl_verify_env.lower() == "true")

    @property
    def enable_logging(self) -> bool:
        return (self._enable_logging_env
                and self._enable_logging_env.lower() == "true")

    @property
    def request_timeout(self) -> int:
        return int(self._request_timeout_env)

    def __call__(self) -> Any:

        self.__validate_inputs()

        group_id = self.__get_group_id(self.group_name)
        if group_id is None:
            raise GroupNotFound(self.group_name)

        if self.__project_exists(group_id, self.project_name):
            raise ProjectAlreadyExistsInTheGroup(self.group_name, group_id, self.project_name)

        created_repo = self.__create_repository_in_group(group_id, self.project_name, self.visibility)
        StkLocalContext().export_repository_url(
            repository_url=created_repo.get("http_url_to_repo")
        )

    def __validate_inputs(self):
        """
        Validates all inputs
        """
        if not self.token or not self.token.strip():
            raise InvalidInputException("The private token ('token') must not be blank.")

        if not self.group_name or not self.group_name.strip():
            raise InvalidInputException("The group name ('group_name') must not be blank.")

        if not self.project_name or not self.project_name.strip():
            raise InvalidInputException("The project name ('project_name') must not be blank.")

        if len(self.project_name.strip()) < 3:
            raise InvalidInputException(
                f"The project name '{self.project_name}' is too short. It must contain at least 3 characters."
            )

        if not self.visibility or not self.visibility.strip():
            raise InvalidInputException("The visibility type ('visibility') must not be blank.")

        if self.visibility not in ["public", "private"]:
            raise InvalidInputException(
                f"The visibility type informed is invalid: '{self.visibility}'. It must be 'public' or 'private'."
            )

    def __get_group_id(self, group_name):
        """
        Gets the Group ID by the informed group name
        """
        print(
            f"> Getting the Group ID by the informed group name '{group_name}'."
        )

        url = f"{self.base_url}/api/v4/groups"
        params = {"search": group_name}

        try:
            response = requests.get(
                url, headers=self.headers, params=params,
                timeout=self.request_timeout, verify=self.enable_ssl_verify
            )
            response.raise_for_status()
            groups = response.json()
            for group in groups:
                if group['name'] == group_name:
                    print(f"> Group ID has been found: '{group['id']}'")
                    return group['id']

            print(f"> Group '{group_name}' not found among all existing groups.")
            return None
        except requests.exceptions.HTTPError as e:
            self.__log_and_raise_error(
                f"Error while searching for group_id by the group name '{group_name}': {e.response.text}"
            )

    def __project_exists(self, group_id, project_name):
        """
        Checks if the project (repository) exists
        """
        print(
            f"> Checking if the project (repository) '{project_name}' exists in the group '{self.group_name}' (group_id={group_id})."
        )

        url = f"{self.base_url}/api/v4/groups/{group_id}/projects"

        try:
            response = requests.get(url, headers=self.headers, timeout=self.request_timeout,
                                    verify=self.enable_ssl_verify)
            response.raise_for_status()
            projects = response.json()
            for project in projects:
                if project['name'] == project_name:
                    return True
                if project['path'] == project_name:
                    return True

            print(
                f"> Project (repository) '{project_name}' not found in the group '{self.group_name}' (group_id={group_id})."
            )
            return False
        except requests.exceptions.HTTPError as e:
            self.__log_and_raise_error(
                f"Error while checking if project (repository) '{project_name}' already exists in the group '{self.group_name} (group_id={group_id})': {e.response.text}"
            )

    def __create_repository_in_group(self, group_id, project_name, visibility):
        """
        Creates a new Gitlab repository (project) in the informed group
        """
        print(
            f"> Creating project (repository) '{project_name}' in the group '{self.group_name}' (group_id={group_id})."
        )

        url = f"{self.base_url}/api/v4/projects"
        data = {
            "name": project_name,
            "namespace_id": group_id,
            "visibility": visibility
        }

        try:
            response = requests.post(
                url, json=data, headers=self.headers,
                timeout=self.request_timeout, verify=self.enable_ssl_verify
            )
            response.raise_for_status()
            print(
                f"> Project (repository) '{project_name}' created in the group '{self.group_name}' with visibility '{visibility}'."
            )
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_message = e.response.text
            if e.response.status_code == 400 and "has already been taken" in e.response.text:
                error_message = "Project already exists in the group. (possible race condition)"

            self.__log_and_raise_error(
                f"Error while creating project (repository) '{project_name}' in the group '{self.group_name}': {error_message}"
            )

    @staticmethod
    def __log_and_raise_error(message):
        """
        Logs error message and raise the main exception
        """
        print(f"> {message}")
        raise GitlabCreateRepoException(message)

    @staticmethod
    def __enable_logging():
        """
        Enables logging for debugging purposes only
        """
        import logging
        import http.client

        http.client.HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True


def run(metadata):
    runner = Runner(metadata)
    runner()
