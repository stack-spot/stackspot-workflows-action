import requests
import time
import base64
import logging
from typing import Optional, Dict

logger = logging.getLogger()


class AzureCreateRepository:
    def __init__(self, org: str, token: str, **_):
        self.api_base_url = f"https://dev.azure.com/{org}"
        auth = base64.b64encode(f":{token}".encode()).decode()
        self.api_headers = {"Authorization": f"Basic {auth}"}

    def get_project(self, project_name: str) -> Optional[Dict]:
        logger.info(f"Getting project '{project_name}' ...")
        url = f"{self.api_base_url}/_apis/projects/{project_name}?api-version=7.0"
        response = requests.get(url, headers=self.api_headers)

        if response.status_code == 200:
            logger.debug("The project already exists.")
            return response.json()

        if response.status_code == 404:
            logger.debug("The project does not exist.")
            return None

        logger.info("Failure getting project.")
        response.raise_for_status()

    def get_repository(self, project_name: str, repo_name: str) -> Optional[Dict]:
        logger.info(f"Getting repository '{repo_name}' ...")
        url = f"{self.api_base_url}/{project_name}/_apis/git/repositories/{repo_name}?api-version=4.1"
        response = requests.get(url, headers=self.api_headers)

        if response.status_code == 200:
            logger.debug("The repository already exists.")
            return response.json()

        elif response.status_code == 404:
            logger.debug("The repository does not exist.")
            return None

        logger.info("Failure getting repository.")
        response.raise_for_status()

    def create_project(self, project_name: str) -> Dict:
        logger.info(f"Creating project '{project_name}' ...")
        url = f"{self.api_base_url}/_apis/projects?api-version=7.0"
        data = {
            "name": project_name,
            "capabilities": {
                "versioncontrol": {"sourceControlType": "Git"},
                "processTemplate": {"templateTypeId": "6b724908-ef14-45cf-84f8-768b5384da45"}
            }
        }
        response = requests.post(url, headers=self.api_headers, json=data)
        response.raise_for_status()

        url = response.json().get("url")
        for i in range(15):
            logger.debug(f"Waiting to finalize the provisioning...")
            time.sleep(5)
            response_check = requests.get(url, headers=self.api_headers)
            status = response_check.json().get("status")
            if status in ["provisioning", "inProgress"]:
                continue
            if status == "succeeded":
                logger.debug(f"The '{project_name}' project successfully created.")
                return response.json()
            else:
                raise Exception(f"Error: Failed to create '{project_name}' project. Status: {status}")
        raise Exception(f"Error: Failed to create '{project_name}' project. Time out.")

    def create_repository(self, project_id: str, repo_name: str) -> Dict:
        logger.info(f"Creating repository '{repo_name}' ...")
        url = f"{self.api_base_url}/_apis/git/repositories?api-version=7.0"
        response = requests.post(url, headers=self.api_headers, json=dict(name=repo_name, project=dict(id=project_id)))
        response.raise_for_status()
        logger.debug(f"The '{repo_name}' repository successfully created.")
        return response.json()

    def __call__(self, project_name: str, name: str, **_) -> str:
        project = self.get_project(project_name=project_name)
        if not project:
            self.create_project(project_name=project_name)
            project = self.get_project(project_name=project_name)
        project_id = project.get("id")

        repository = (self.get_repository(project_name=project_name, repo_name=name) or
                      self.create_repository(project_id=project_id, repo_name=name))
        return repository.get("remoteUrl")
