import logging
import requests


CREATE_PROJECT_SERVICE_URL = "https://{domain}/v4/projects"
CREATE_TRIGGER_SERVICE_URL = "https://{domain}/v4/projects/{project_id}/triggers"
CREATE_MERGE_REQUEST_SERVICE_URL = "https://{domain}/v4/projects/{project_id}/merge_requests"


class GitlabApiClient:
    def __init__(self, **kwargs):
        self.http_client = kwargs.get("http_client", requests)
        self.pat = kwargs.get("pat")
        self.domain = "gitlab.com/api"

    def create_project(self, project_name: str):
        logging.info("Gitlab create project...")
        return self.http_client.post(
            url=CREATE_PROJECT_SERVICE_URL.format(domain=self.domain),
            json=dict(
                name='Stackspot workflows',
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
            json=dict(description="Stackspot workflow trigger token"),
        )

    def create_merge_request(self, project_id: str, pr_title: str, pr_description: str, source_branch: str, target_branch: str):
        logging.info("Gitlab create merge request...")
        return self.http_client.post(
            url=CREATE_MERGE_REQUEST_SERVICE_URL.format(domain=self.domain, project_id=project_id),
            json=dict(
                title=pr_title,
                description=pr_description,
                source_branch=source_branch,
                target_branch=target_branch,
            )
        )
