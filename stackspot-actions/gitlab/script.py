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


class Runner:
    def __init__(self, metadata, base_url="https://gitlab.com") -> None:
        self.base_url = base_url
        self.group_name = metadata.inputs.get("org")
        self.project_name = metadata.inputs.get("project_name")
        self.visibility = metadata.inputs.get("visibility", "private")  # default=private
        self.token = metadata.inputs.get("token")
        self.enable_ssl_verify = metadata.inputs.get("dev__enable_ssl_verify", True)  # default=enabled
        self.enable_logging = metadata.inputs.get("dev__enable_logging", False)  # default=disabled
        self.default_timeout = metadata.inputs.get("dev__default_timeout", 10)  # default=10s
        self.headers = {
            "Private-Token": self.token,
            "Content-Type": "application/json"
        }
        if self.enable_logging:
            self.__enable_logging()

    def __call__(self) -> Any:

        self.__validate_inputs()

        group_id = self.__get_group_id(self.group_name)
        if group_id is None:
            raise GroupNotFound(self.group_name)

        if self.__project_exists(group_id, self.project_name):
            raise ProjectAlreadyExistsInTheGroup(self.group_name, group_id, self.project_name)

        self.__create_repository_in_group(group_id, self.project_name, self.visibility)

    def __validate_inputs(self):
        """
        Validates all inputs
        """
        if not self.group_name or not self.group_name.strip():
            raise InvalidInputException("The group name ('org') must not be blank.")

        if not self.token or not self.token.strip():
            raise InvalidInputException("The private token ('token') must not be blank.")

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
                timeout=self.default_timeout, verify=self.enable_ssl_verify
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
            response = requests.get(url, headers=self.headers, timeout=self.default_timeout,
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
                timeout=self.default_timeout, verify=self.enable_ssl_verify
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
