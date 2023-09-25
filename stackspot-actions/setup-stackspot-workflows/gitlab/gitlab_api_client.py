import logging
import requests


GET_PROJECT_SERVICE_URL = "https://{domain}/v4/projects/{project_id}"
CREATE_PROJECT_SERVICE_URL = "https://{domain}/v4/projects"
CREATE_TRIGGER_SERVICE_URL = "https://{domain}/v4/projects/{project_id}/triggers"
CREATE_MERGE_REQUEST_SERVICE_URL = "https://{domain}/v4/projects/{project_id}/merge_requests"


class GitlabApiClient:
    def __init__(self, **kwargs):
        self.http_client = kwargs.get("http_client", requests)
        self.pat = kwargs.get("pat")
        self.domain = "gitlab.com/api"
        self.auth_params = dict(private_token=self.pat)

    def create_project(self, project_name: str):
        logging.info("Gitlab create project...")
        return self.http_client.post(
            url=CREATE_PROJECT_SERVICE_URL.format(domain=self.domain),
            params=self.auth_params,
            json=dict(
                name=project_name,
                description="This repository contains stackspot workflow runner",
                path=project_name,
                initialize_with_readme="true",
                default_branch="main"
            )
        )

    def create_trigger(self, project_id: str) -> requests.Response:
        logging.info("Gitlab create trigger...")
        return self.http_client.post(
            url=CREATE_TRIGGER_SERVICE_URL.format(domain=self.domain, project_id=project_id),
            params=self.auth_params,
            json=dict(description="Stackspot workflow trigger token"),
        )

    def create_merge_request(self, project_id: str, pr_title: str, pr_description: str, source_branch: str, target_branch: str):
        logging.info("Gitlab create merge request...")
        return self.http_client.post(
            url=CREATE_MERGE_REQUEST_SERVICE_URL.format(domain=self.domain, project_id=project_id),
            params=self.auth_params,
            json=dict(
                title=pr_title,
                description=pr_description,
                source_branch=source_branch,
                target_branch=target_branch,
            )
        )

    def get_project(self, group_name: str, project_name: str):
        logging.info("Gitlab get project request...")
        return self.http_client.get(
            url=GET_PROJECT_SERVICE_URL.format(domain=self.domain, project_id=f"{group_name}%2F{project_name}"),
            params=self.auth_params
        )
