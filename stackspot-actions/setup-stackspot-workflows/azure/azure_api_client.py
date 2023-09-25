import base64
import logging
import requests

CREATE_PROJECT_SERVICE_URL = "https://{domain}/{org_name}/_apis/projects/{project_name}"
GET_PROJECT_SERVICE_URL = "https://{domain}/{org_name}/_apis/projects/{project_name}"
CREATE_PULL_REQUEST_SERVICE_URL = "https://{domain}/{org_name}/_apis/repositories/{repository_id}/pullrequests"
CREATE_PIPELINE_SERVICE_URL = "https://{domain}/{org_name}/{project_name}/_apis/pipelines"
GET_REPOSITORY_ID_SERVICE_URL = "https://{domain}/{org_name}/{project_name}/_apis/git/repositories/{repository_name}"
CREATE_SERVICE_ENDPOINT_SERVICE_URL = "https://{domain}/{org_name}/{project_name}/_apis/serviceendpoint/endpoints"
UPDATE_PIPELINE_PERMISSION_ENDPOINT_SERVICE_URL = "https://{domain}/{org_name}/{project_name}/_apis/pipelines/pipelinePermissions/endpoint/{endpoint_id}"


class AzureApiClient:
    def __init__(self, **kwargs):
        self.http_client = kwargs.get("http_client", requests)
        self.pat = kwargs.get("pat")
        self.api_version = {"api-version": "7.0"}
        self.authorization = {"Authorization": f'Basic {base64.b64encode(f"user:{self.pat}".encode()).decode("utf-8")}'}
        self.domain = "dev.azure.com"

    def create_pipeline(self, org_name: str, project_name: str, repository_id: str, pipeline_name: str) -> requests.Response:
        logging.info("Azure create pipeline...")
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
        )

    def get_repository(self, org_name: str, project_name: str, repository_name: str) -> requests.Response:
        logging.info("Azure get repository...")
        return self.http_client.get(
            url=GET_REPOSITORY_ID_SERVICE_URL.format(domain=self.domain, org_name=org_name, project_name=project_name, repository_name=repository_name),
            params=self.api_version,
            headers=self.authorization,
        )

    def get_project(self, org_name: str, project_name: str) -> requests.Response:
        logging.info("Azure get project...")
        return self.http_client.get(
            url=GET_PROJECT_SERVICE_URL.format(domain=self.domain, org_name=org_name, project_name=project_name),
            params=self.api_version,
            headers=self.authorization,
        )

    def create_service_endpoint(self, org_name: str, project_name: str, github_pat: str, project_id: str) -> requests.Response:
        logging.info("Azure create service endpoint...")
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
            }
        )

    def update_pipeline_permission_endpoint(self, org_name: str, project_name: str, endpoint_id: str) -> requests.Response:
        logging.info("Azure update pipeline permission endpoint...")
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
            }
        )

    def create_pull_request(self, repository_id: str, pr_title: str, pr_description: str, pr_target: str, pr_source: str) -> requests.Response:
        logging.info("Azure create pull request...")
        return self.http_client.post(
            url=CREATE_PULL_REQUEST_SERVICE_URL.format(domain=self.domain, repository_id=repository_id),
            params=self.api_version,
            headers=self.authorization,
            json={
                "sourceRefName": f"refs/heads/{pr_source}",
                "targetRefName": f"refs/heads/{pr_target}",
                "title": pr_title,
                "description": pr_description,
            }
        )

    def create_project(self, org_name: str, project_name: str) -> requests.Response:
        logging.info("Azure create project...")
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
            }
        )
