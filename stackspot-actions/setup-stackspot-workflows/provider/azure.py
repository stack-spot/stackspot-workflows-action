import base64
import logging
import requests
from typing import Mapping

from .handle_errors import handle_api_response_errors
from .provider import Provider, Inputs
from .errors import NotFoundError


class UrlBuilder:
    def __init__(self, inputs: Inputs):
        self.inputs = inputs
        self.base_url = f"https://dev.azure.com/{inputs.org_name}"
        self.paths = []

    def path(self, path: str) -> "UrlBuilder":
        self.paths.append(path)
        return self

    def build(self) -> str:
        return "/".join([self.base_url, *self.paths])


class AzureProvider(Provider):
    def __init__(self):
        self.default_params = {
            "api-version": "7.0",
        }

    def __default_headers(self, inputs: Inputs) -> Mapping[str, str]:
        return {
            "Authorization": self.__basic_auth(inputs),
        }

    def __basic_auth(self, inputs: Inputs) -> str:
        auth_str = f"user:{inputs.pat}"
        auth_bytes = auth_str.encode()
        auth_b64_bytes = base64.b64encode(auth_bytes)
        return f"Basic {auth_b64_bytes.decode()}"

    def __setup_pipeline(self, name: str, inputs: Inputs, repo_id: str):
        logging.info("Configuring pipeline %s...", name)
        url = UrlBuilder(inputs).path(inputs.repo_name).path("_apis").path("pipelines").build()
        response = requests.post(
            url,
            headers=self.__default_headers(inputs),
            params=self.default_params,
            json={
                "name": name,
                "folder": "\\",
                "configuration": {
                    "type": "yaml",
                    "path": f"{name}.yml",
                    "variables": {
                        "secret_git": {
                            "isSecret": True
                        },
                        "secret_stk_login": {
                            "isSecret": True
                        }
                    },
                    "repository": {
                        "id": repo_id,
                        "type": "azureReposGit"
                    },
                }
            }
        )
        if response.status_code == 409:
            logging.warning(f"{name} pipeline already exists")
        else:
            handle_api_response_errors(response)

    def __setup_github_connection(self, inputs: Inputs):
        logging.info("Setting up github service connection...")
        project_id = self.__get_project_id(inputs)
        url = UrlBuilder(inputs).path(inputs.repo_name).path("_apis").path("serviceendpoint").path("endpoints").build()
        body = {
            "name": "stackspot_github_connection",
            "description": "Connection to StackSpot github",
            "type": "github",
            "url": "https://github.com",
            "authorization": {
                "scheme": "Token",
                "parameters": {
                    "AccessToken": inputs.github_pat,
                    "apitoken": ""
                }
            },
            "serviceEndpointProjectReferences": [
                {
                    "projectReference": {
                        "id": project_id,
                        "name": inputs.repo_name
                    },
                    "name": "stackspot_github_connection",
                    "description": "Connection to StackSpot github"
                }
            ]
        }
        response = requests.post(
            url,
            headers=self.__default_headers(inputs),
            params=self.default_params,
            json=body
        )
        response_json = response.json()
        if response.status_code == 500 and "DuplicateServiceConnectionException" in response_json.get("typeName"):
            logging.warning("Git connection already exists with name stackspot_github_connection")
            return
        else:
            handle_api_response_errors(response)


        endpoint_id = response.json()["id"]
        url = UrlBuilder(inputs).path(inputs.repo_name).path("_apis").path("pipelines").path(
            "pipelinePermissions").path("endpoint").path(endpoint_id).build()
        body = {
            "resource": {
                "id": endpoint_id,
                "type": "endpoint",
                "name": ""
            },
            "pipelines": [],
            "allPipelines": {
                "authorized": True,
                "authorizedBy": None,
                "authorizedOn": None
            }
        }
        response = requests.patch(
            url,
            headers=self.__default_headers(inputs),
            params={
                "api-version": "7.0-preview",
            },
            json=body
        )
        handle_api_response_errors(response)

    def __get_repo_id(self, inputs: Inputs) -> str:
        url = UrlBuilder(inputs).path(inputs.repo_name).path("_apis").path("git").path("repositories").path(
            inputs.repo_name).build()
        response = requests.get(
            url,
            headers=self.__default_headers(inputs),
            params=self.default_params,
        )
        handle_api_response_errors(response)
        return response.json()["id"]

    def __get_project_id(self, inputs: Inputs) -> str:
        get_project_url = UrlBuilder(inputs).path("_apis").path("projects").path(inputs.repo_name).build()
        response = requests.get(
            url=get_project_url,
            headers=self.__default_headers(inputs),
            params=self.default_params
        )
        handle_api_response_errors(response)
        return response.json()["id"]

    def execute_pre_setup_provider(self, inputs: Inputs):
        #  Ignored due to not needing to perform even a step before the clone
        pass

    def create_pull_request(self, inputs: Inputs) -> str:
        repo_id = self.__get_repo_id(inputs)
        pull_request_url = UrlBuilder(inputs).path("_apis").path("git").path("repositories").path(repo_id).path("pullrequests").build()
        body = {
            "sourceRefName": f"refs/heads/{inputs.ref_branch}",
            "targetRefName": "refs/heads/main",
            "title": "Stackspot Update workflow configuration.",
            "description": "Automatically created pull request."
        }
        response = requests.post(
            pull_request_url,
            headers=self.__default_headers(inputs),
            params=self.default_params,
            json=body
        )
        handle_api_response_errors(response)
        response_json = response.json()
        print(response_json)

    def execute_repo_creation(self, inputs: Inputs):
        create_project_url = UrlBuilder(inputs).path("_apis").path("projects").build()
        print(f"create_project_url: {create_project_url}")
        body = {
            "name": inputs.repo_name,
            "description": "StackSpot workflows",
            "visibility": "private",
            "capabilities": {
                "versioncontrol": {
                    "sourceControlType": "Git"
                },
                "processTemplate": {
                    "templateTypeId": "6b724908-ef14-45cf-84f8-768b5384da45"
                }
            }
        }
        logging.info(create_project_url)
        response = requests.post(
            url=create_project_url,
            headers=self.__default_headers(inputs),
            params=self.default_params,
            json=body
        )
        handle_api_response_errors(response)

    def repo_exists(self, inputs: Inputs) -> bool:
        try:
            self.__get_project_id(inputs)
            return True
        except NotFoundError:
            return False
        except:
            raise

    def clone_url(self, inputs: Inputs) -> str:
        return f"https://{inputs.org_name}:{inputs.pat}@dev.azure.com/{inputs.org_name}/{inputs.repo_name}/_git/{inputs.repo_name}"

    def execute_provider_setup(self, inputs: Inputs):
        repo_id = self.__get_repo_id(inputs)
        self.__setup_pipeline("middle-flow", inputs, repo_id)
        self.__setup_github_connection(inputs)
