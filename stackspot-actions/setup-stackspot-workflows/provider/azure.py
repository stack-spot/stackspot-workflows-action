import base64
import logging
import requests
from typing import Mapping
from .provider import Provider, Inputs
from .errors import UnauthorizedError, NotFoundError

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
    
    def __handle_api_response_errors(self, response: requests.Response) -> bool:
        if response.ok:
            return True
        match response.status_code:
            case requests.codes.not_found:
                raise NotFoundError()
            case requests.codes.unauthorized:
                raise UnauthorizedError()
        logging.error("Error response body: %s", response.text)
        response.raise_for_status()
    

    def __setup_pipeline(self, name: str, inputs: Inputs):
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
                        "id": "63a33171-ad49-4c9b-b4f1-a8663c048840",
                        "type": "azureReposGit"
                    },
                }
            }
        )
        self.__handle_api_response_errors(response)

    def execute_repo_creation(self, inputs: Inputs):
        create_project_url = UrlBuilder(inputs).path("_apis").path("projects").build()
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
        response = requests.post(
            url=create_project_url,
            headers=self.__default_headers(inputs),
            params=self.default_params,
            json=body
        )
        self.__handle_api_response_errors(response)


    def repo_exists(self, inputs: Inputs) -> bool:
        get_project_url = UrlBuilder(inputs).path("_apis").path("projects").path(inputs.repo_name).build()
        response = requests.get(
            url=get_project_url,
            headers=self.__default_headers(inputs),
            params=self.default_params
        )
        try:
            self.__handle_api_response_errors(response)
            return True
        except NotFoundError:
            return False
        except:
            raise

    def clone_url(self, inputs: Inputs) -> str:
        return f"https://{inputs.org_name}:{inputs.pat}@dev.azure.com/{inputs.org_name}/{inputs.repo_name}/_git/{inputs.repo_name}"
    
    def execute_provider_setup(self, inputs: Inputs):
        self.__setup_pipeline("create-app", inputs)
        self.__setup_pipeline("create-infra", inputs)
        self.__setup_pipeline("run-action", inputs)