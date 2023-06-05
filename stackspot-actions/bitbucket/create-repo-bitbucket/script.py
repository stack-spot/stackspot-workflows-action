import json
from typing import Any
import requests


class BitbucketCreateRepoException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class WorkspaceNotFound(BitbucketCreateRepoException):
    def __init__(self, workspace):
        super().__init__(f"The {workspace} workspace was not found.")


class WorkspaceExistsGeneralError(BitbucketCreateRepoException):
    def __init__(self, err):
        super().__init__(
            f"An error ocurred while checking if the workspace exists: {err}"
        )


class ProjectNameTooShort(BitbucketCreateRepoException):
    def __init__(self, project_name):
        super().__init__(
            f"The name {project_name} is too short. It must contain at least 3 characters."
        )


class ProjectCreationError(BitbucketCreateRepoException):
    def __init__(self, err):
        super().__init__(f"An error ocurred while creating the project: {err}")


class RepositoryExistsGeneralError(BitbucketCreateRepoException):
    def __init__(self, err):
        super().__init__(
            f"An error ocurred while checking if the repository exists: {err}"
        )


class CreateRepositoryError(BitbucketCreateRepoException):
    def __init__(self, err):
        super().__init__(f"An error ocurred while creating the repository: {err}")


class Runner:
    def __init__(self, metadata) -> None:
        self.base_url = "https://api.bitbucket.org/2.0"
        inputs = metadata.inputs
        token = inputs.get("token")
        self.get_headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        self.post_headers = {"Content-Type": "application/json"}
        self.post_headers.update(self.get_headers)

        self.workspace_name = inputs.get("org")
        self.project_name = inputs.get("project_name")
        self.repo_name = inputs.get("name")

    def __call__(self) -> Any:
        self.__workspace_exists()
        if not self.__repository_exists():
            project_key = self.__project_exists()
            if not project_key:
                project_key = self.__create_project()
            self.__create_repository(project_key)

    def __workspace_exists(self):
        """
        Checks if the workspace exists
        Workspaces can not be created by API integration
        """
        print(
            f"> Checking if the '{self.workspace_name}' workspace exists in your organization."
        )

        url = f"{self.base_url}/workspaces/{self.workspace_name}/permissions"

        try:
            response = requests.get(url, headers=self.get_headers)
            response.raise_for_status()
            print(f"> Workspace '{self.workspace_name}' found.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in (
                requests.codes.not_found,
                requests.codes.forbidden,
                requests.codes.unauthorized,
            ):
                raise WorkspaceNotFound(self.workspace_name)
            raise WorkspaceExistsGeneralError(e)

    def __repository_exists(self):
        """
        Checks if the repository exists
        """
        print(
            f"> Checking if the '{self.repo_name}' repository exists in the workspace {self.workspace_name}."
        )

        url = f"{self.base_url}/repositories/{self.workspace_name}/{self.repo_name}"

        try:
            response = requests.get(url, headers=self.get_headers)
            response.raise_for_status()
            print(f">'{self.repo_name}' already exists.")
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == requests.codes.not_found:
                print(f">'{self.repo_name}' not found. It will be created.")
                return False
            raise RepositoryExistsGeneralError(e)

    def __project_exists(self):
        """
        Checks if the informed project exists
        """
        print(
            f"> Checking if the '{self.project_name}' project exists in the workspace {self.workspace_name}."
        )
        url = f"{self.base_url}/workspaces/{self.workspace_name}/projects"

        try:
            response = requests.get(url, self.get_headers)
            response.raise_for_status()
            data = response.json()
            values = data.get("values", [])
            project_exists = [
                val
                for val in values
                if val.get("key") == self.project_name
                or val.get("name") == self.project_name
            ]
            if project_exists:
                print(
                    f"> Project '{self.project_name}' project found in the workspace {self.workspace_name}."
                )
                project = project_exists.pop()
                return project.get("key")
        except requests.exceptions.HTTPError as e:
            print(
                f"> Project '{self.project_name}' not found in the workspace {self.workspace_name}."
            )
            if e.response.status_code == requests.codes.not_found:
                return None

    def __create_project(self):
        """
        Creates a new Bitbucket Project in the workspace
        """
        print(
            f"> Creating project '{self.project_name}' in the workspace {self.workspace_name}."
        )
        url = f"{self.base_url}/workspaces/{self.workspace_name}/projects"

        if len(self.project_name) < 3:
            raise ProjectNameTooShort(self.project_name)

        key = (
            self.project_name.replace(" ", "")
            .replace("_", "")
            .replace("-", "")[:3]
            .upper()
        )
        print(f"> Project key set to {key}")

        payload = json.dumps({"name": self.project_name, "key": key})

        try:
            response = requests.post(url, headers=self.post_headers, data=payload)
            response.raise_for_status()
            print(
                f"> Project '{self.project_name}' created in the workspace {self.workspace_name}."
            )
        except requests.exceptions.HTTPError as e:
            raise ProjectCreationError(e)

        return key

    def __create_repository(self, project_key: str):
        """
        Creates a new repository on bitbucket
        """
        print(f"> Creating repository '{self.repo_name}' in the project {project_key}.")

        url = f"{self.base_url}/repositories/{self.workspace_name}/{self.repo_name}"

        payload = json.dumps(
            {
                "scm": "git",
                "project": {"key": project_key},
            }
        )

        try:
            response = requests.post(url, data=payload, headers=self.post_headers)
            response.raise_for_status()
            print(f"Repository {self.repo_name} successfully created.")
        except requests.exceptions.HTTPError as e:
            raise CreateRepositoryError(e)


def run(metadata):
    runner = Runner(metadata)
    runner()
