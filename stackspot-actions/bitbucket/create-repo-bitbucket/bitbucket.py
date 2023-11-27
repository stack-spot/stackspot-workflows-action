import json
import requests
import logging
from typing import Any

logger = logging.getLogger()


class BitbucketCreateRepository:

    def __init__(self, org: str, token: str, **_):
        self.base_url = "https://api.bitbucket.org/2.0"
        self.get_headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        self.post_headers = {"Content-Type": "application/json"}
        self.post_headers.update(self.get_headers)
        self.workspace_name = org

    def __call__(self, project_name: str, name: str, visibility: str = "PRIVATE") -> Any:
        self.workspace_exists()
        if not self.repository_exists(repo_name=name):
            project_key = self.get_project_key(project_name=project_name)
            if not project_key:
                project_key = self.create_project(project_name=project_name)
            self.create_repository(project_key=project_key, repo_name=name, visibility=visibility)

    def workspace_exists(self):
        logger.info(f"Checking if the '{self.workspace_name}' workspace exists in your organization ...")
        url = f"{self.base_url}/workspaces/{self.workspace_name}/permissions"
        response = requests.get(url, headers=self.get_headers)
        response.raise_for_status()

    def repository_exists(self, repo_name: str):
        logger.info(f"Checking if the '{repo_name}' repository exists in the workspace {self.workspace_name} ...")
        url = f"{self.base_url}/repositories/{self.workspace_name}/{repo_name}"

        response = requests.get(url, headers=self.get_headers)
        if response.ok:
            return True
        elif response.status_code == requests.codes.not_found:
            return False
        response.raise_for_status()

    def get_project_key(self, project_name: str):
        logger.info(f"Checking if the '{project_name}' project exists in the workspace {self.workspace_name} ...")
        url = f"{self.base_url}/workspaces/{self.workspace_name}/projects"
        response = requests.get(url, self.get_headers)
        if response.ok:
            data = response.json()
            values = data.get("values", [])
            project_exists = [val for val in values if val.get("key") == project_name or val.get("name") == project_name]
            if project_exists:
                logger.info(f"Project '{project_name}' project found in the workspace {self.workspace_name}.")
                project = project_exists.pop()
                return project.get("key")
        if response.status_code == requests.codes.not_found:
            return None
        response.raise_for_status()

    def project_key_exists(self, key: str):
        logger.info(f"Checking if the '{key}' exists.")
        url = f"{self.base_url}/workspaces/{self.workspace_name}/projects/{key}"
        response = requests.get(url, self.get_headers)
        if response.ok:
            return True
        elif response.status_code == requests.codes.not_found:
            return False
        response.raise_for_status()

    def create_project(self, project_name: str):
        logger.info(f"Creating project '{project_name}' in the workspace {self.workspace_name} ...")
        k = project_name.replace(" ", "").replace("_", "").replace("-", "").upper()

        key = k
        i = 0
        while not self.project_key_exists(key):
            i += 1
            key = f"{k}{i}"

        logger.info(f"Project key set to {key}")
        url = f"{self.base_url}/workspaces/{self.workspace_name}/projects"
        response = requests.post(url, headers=self.post_headers, data=json.dumps(dict(name=project_name, key=key)))
        response.raise_for_status()
        return key

    def create_repository(self, project_key: str, repo_name: str, visibility: str):
        logger.info(f"Creating repository '{repo_name}' in the project {project_key} ...")
        url = f"{self.base_url}/repositories/{self.workspace_name}/{repo_name}"
        data = json.dumps(dict(scm="git", project=dict(key=project_key), is_private=visibility == "PRIVATE"))
        response = requests.post(url, data=data, headers=self.post_headers)
        response.raise_for_status()
