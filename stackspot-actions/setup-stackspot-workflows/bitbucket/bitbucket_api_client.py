import requests
import logging


AUTH_SERVICE_URL = "https://bitbucket.org/site/oauth2/access_token"
GET_REPOSITORY_SERVICE_URL = "https://{domain}/2.0/repositories/{workspace_name}/{repository_name}"
GET_PROJECTS_SERVICE_URL = "https://{domain}/2.0/workspaces/{workspace_name}/projects/{project_name}"
CREATE_REPOSITORY_SERVICE_URL = "https://{domain}/2.0/repositories/{workspace_name}/{repository_name}"
CREATE_PULL_REQUEST_SERVICE_URL = "https://{domain}/2.0/repositories/{workspace_name}/{repository_name}/pullrequests"
GET_REPOSITORY_VARIABLE_SERVICE_URL = "https://{domain}/2.0/repositories/{workspace_name}/{repository_name}/pipelines_config/variables"
PUT_REPOSITORY_PIPELINE_SERVICE_URL = "https://{domain}/2.0/repositories/{workspace_name}/{repository_name}/pipelines_config"


class BitbucketApiClient:
    def __init__(self, **kwargs):
        self.http_client = kwargs.get("http_client")
        self.domain = "api.bitbucket.org"
        self.client_key = kwargs.get("client_key")
        self.client_secret = kwargs.get("client_secret")
        self.auth = (self.client_key, self.client_secret)
        self.authorization = None
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    @property
    def authorization_header(self):
        if not self.authorization:
            result = self.http_client.post(
                url=AUTH_SERVICE_URL.format(domain=self.domain),
                data=dict(grant_type="client_credentials"),
                auth=self.auth,
                title="bitbucket authentication",
                raise_for_status=True
            )
            self.authorization = result.json()['access_token']
        return {"Authorization": f"Bearer {self.authorization}"}

    def get_repository(self, workspace_name: str, repository_name: str, raise_for_status: bool = True) -> requests.Response:
        return self.http_client.get(
            url=GET_REPOSITORY_SERVICE_URL.format(domain=self.domain, workspace_name=workspace_name, repository_name=repository_name),
            headers=dict(**self.authorization_header),
            title="bitbucket get repository",
            raise_for_status=raise_for_status
        )

    def create_pull_request(self, workspace_name: str, repository_name: str, pr_title: str, pr_source: str, pr_destination: str) -> requests.Response:
        return self.http_client.post(
            url=CREATE_PULL_REQUEST_SERVICE_URL.format(domain=self.domain, workspace_name=workspace_name, repository_name=repository_name),
            headers=dict(**self.authorization_header),
            json={
                "title": pr_title,
                "source": {"branch": {"name": pr_source}},
                "destination": {"branch": {"name": pr_destination}},
            },
            title="bitbucket create pull request",
            raise_for_status=True
        )

    def create_repository(self, workspace_name: str, repository_name: str, project_key: str):
        return self.http_client.post(
            url=CREATE_REPOSITORY_SERVICE_URL.format(domain=self.domain, workspace_name=workspace_name, repository_name=repository_name),
            headers=dict(**self.authorization_header),
            json={
                "scm": "git",
                "is_private": True,
                "project": {"key": project_key},
            },
            title="bitbucket create repository",
            raise_for_status=True
        )

    def get_projects(self, workspace_name: str, project_name: str):
        return self.http_client.get(
            url=GET_PROJECTS_SERVICE_URL.format(domain=self.domain, workspace_name=workspace_name, project_name=project_name),
            headers=dict(**self.authorization_header),
            title="bitbucket get project",
            raise_for_status=True,
        )

    def update_repository_pipeline(self, workspace_name: str, repository_name: str):
        return self.http_client.put(
            url=PUT_REPOSITORY_PIPELINE_SERVICE_URL.format(domain=self.domain, workspace_name=workspace_name, repository_name=repository_name),
            headers=dict(**self.authorization_header),
            json=dict(enabled=True),
            title="bitbucket update repository pypeline",
            raise_for_status=True,
        )
