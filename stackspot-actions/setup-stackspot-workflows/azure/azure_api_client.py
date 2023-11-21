import base64
import requests

CREATE_PROJECT_SERVICE_URL = "https://{domain}/{org_name}/_apis/projects/{project_name}"
GET_PROJECT_SERVICE_URL = "https://{domain}/{org_name}/_apis/projects/{project_name}"
CREATE_PULL_REQUEST_SERVICE_URL = "https://{domain}/{org_name}/{project_name}/_apis/git/repositories/{respository_name}/pullrequests"
CREATE_PIPELINE_SERVICE_URL = "https://{domain}/{org_name}/{project_name}/_apis/pipelines"
CREATE_REPOSITORY_SERVICE_URL = "https://{domain}/{org_name}/_apis/git/repositories"
GET_REPOSITORY_ID_SERVICE_URL = "https://{domain}/{org_name}/{project_name}/_apis/git/repositories/{repository_name}"
CREATE_SERVICE_ENDPOINT_SERVICE_URL = "https://{domain}/{org_name}/{project_name}/_apis/serviceendpoint/endpoints"
UPDATE_PIPELINE_PERMISSION_ENDPOINT_SERVICE_URL = "https://{domain}/{org_name}/{project_name}/_apis/pipelines/pipelinePermissions/endpoint/{endpoint_id}"


class AzureApiClient:
    def __init__(self, **kwargs):
        self.http_client = kwargs.get("http_client")
        self.pat = kwargs.get("pat")
        self.api_version = {"api-version": "7.0"}
        self.authorization = {"Authorization": f'Basic {base64.b64encode(f"user:{self.pat}".encode()).decode("utf-8")}'}
        self.domain = "dev.azure.com"

    def create_pipeline(self, org_name: str, project_name: str, repository_id: str, pipeline_name: str, raise_for_status: bool = True) -> requests.Response:
        return self.http_client.post(
            url=CREATE_PIPELINE_SERVICE_URL.format(domain=self.domain, org_name=org_name, project_name=project_name),
            params=self.api_version,
            headers=self.authorization,
            json={
                "name": pipeline_name,
                "folder": "\\",
                "configuration": {
                    "type": "yaml",
                    "path": f"{pipeline_name}.yml",
                    "variables": {
                        "secret_git": {"isSecret": True},
                        "secret_stk_login": {"isSecret": True},
                    },
                    "repository": {"id": repository_id, "type": "azureReposGit"},
                },
            },
            title="azure create pipeline",
            raise_for_status=raise_for_status,
        )

    def get_repository(self, org_name: str, project_name: str, repository_name: str, raise_for_status: bool = True) -> requests.Response:
        return self.http_client.get(
            url=GET_REPOSITORY_ID_SERVICE_URL.format(domain=self.domain, org_name=org_name, project_name=project_name, repository_name=repository_name),
            params=self.api_version,
            headers=self.authorization,
            title="azure get repository",
            raise_for_status=raise_for_status,
        )

    def get_project(self, org_name: str, project_name: str, raise_for_status: bool = True) -> requests.Response:
        return self.http_client.get(
            url=GET_PROJECT_SERVICE_URL.format(domain=self.domain, org_name=org_name, project_name=project_name),
            params=self.api_version,
            headers=self.authorization,
            title="azure get project",
            raise_for_status=raise_for_status,
        )

    def create_project(self, org_name: str, project_name: str) -> requests.Response:
        return self.http_client.post(
            url=CREATE_PROJECT_SERVICE_URL.format(domain=self.domain, org_name=org_name, project_name=project_name),
            params=self.api_version,
            headers=self.authorization,
            json={
                "name": project_name,
                "description": "StackSpot workflows",
                "visibility": "private",
                "capabilities": {
                    "versioncontrol": {"sourceControlType": "Git"},
                    "processTemplate": {
                        "templateTypeId": "6b724908-ef14-45cf-84f8-768b5384da45"
                    },
                },
            },
            title="azure create project",
            raise_for_status=True,
        )

    def create_repository(self, org_name: str, project_id: str, repository_name: str) -> requests.Response:
        return self.http_client.post(
            url=CREATE_REPOSITORY_SERVICE_URL.format(domain=self.domain, org_name=org_name),
            params=self.api_version,
            headers=self.authorization,
            json={
                "name": repository_name,
                "project": {
                    "id": project_id
                }
            },
            title="azure create repository",
            raise_for_status=True,
        )

    def create_service_endpoint(self, org_name: str, project_name: str, github_pat: str, project_id: str, raise_for_status: bool = True) -> requests.Response:
        return self.http_client.post(
            url=CREATE_SERVICE_ENDPOINT_SERVICE_URL.format(domain=self.domain, org_name=org_name, project_name=project_name),
            params=self.api_version,
            headers=self.authorization,
            json={
                "name": "stackspot_github_connection",
                "description": "Connection to StackSpot github",
                "type": "github",
                "url": "https://github.com",
                "authorization": {
                    "scheme": "Token",
                    "parameters": {"AccessToken": github_pat, "apitoken": ""},
                },
                "serviceEndpointProjectReferences": [
                    {
                        "projectReference": {"id": project_id, "name": project_name},
                        "name": "stackspot_github_connection",
                        "description": "Connection to StackSpot github",
                    }
                ],
            },
            title="azure create service endpoint",
            raise_for_status=raise_for_status,
        )

    def update_pipeline_permission_endpoint(self, org_name: str, project_name: str, endpoint_id: str) -> requests.Response:
        return self.http_client.patch(
            url=UPDATE_PIPELINE_PERMISSION_ENDPOINT_SERVICE_URL.format(domain=self.domain, org_name=org_name, project_name=project_name, endpoint_id=endpoint_id),
            params={"api-version": "7.0-preview"},
            headers=self.authorization,
            json={
                "resource": {"id": endpoint_id, "type": "endpoint", "name": ""},
                "pipelines": [],
                "allPipelines": {
                    "authorized": True,
                    "authorizedBy": None,
                    "authorizedOn": None,
                },
            },
            title="azure update pipeline permission endpoint",
            raise_for_status=True,
        )

    def create_pull_request(self, org_name: str, respository_name: str, project_name: str, pr_title: str, pr_description: str, pr_target: str, pr_source: str) -> requests.Response:
        return self.http_client.post(
            url=CREATE_PULL_REQUEST_SERVICE_URL.format(domain=self.domain, org_name=org_name, project_name=project_name, respository_name=respository_name),
            params=self.api_version,
            headers=self.authorization,
            json={
                "sourceRefName": f"refs/heads/{pr_source}",
                "targetRefName": f"refs/heads/{pr_target}",
                "title": pr_title,
                "description": pr_description,
            },
            title="azure create pull request",
            raise_for_status=True,
        )
