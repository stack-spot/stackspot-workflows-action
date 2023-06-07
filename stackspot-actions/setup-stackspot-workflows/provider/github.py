import requests
import logging
from .errors import NotFoundError
from .handle_errors import handle_api_response_errors
from .provider import Provider, Inputs


class UrlBuilder:
    def __init__(self, inputs: Inputs):
        self.inputs = inputs
        self.base_url = f" https://api.github.com"
        self.paths = []

    def path(self, path: str) -> "UrlBuilder":
        self.paths.append(path)
        return self

    def build(self) -> str:
        return "/".join([self.base_url, *self.paths])


class GithubProvider(Provider):
    def __default_headers(self, inputs: Inputs):
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {inputs.pat}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def __repo_info(self, inputs: Inputs) -> dict:
        url_builder = (
            UrlBuilder(inputs)
            .path("repos")
            .path(inputs.org_name)
            .path(inputs.repo_name)
        )
        return self.__get(url_builder, inputs)

    def __get(self, url_builder: UrlBuilder, inputs: Inputs) -> dict:
        response = requests.get(
            url_builder.build(),
            headers=self.__default_headers(inputs),
            verify=False,
        )
        handle_api_response_errors(response)
        return response.json()

    def __post(self, url_builder: UrlBuilder, inputs: Inputs, body: dict) -> dict:
        response = requests.post(
            url_builder.build(),
            headers=self.__default_headers(inputs),
            json=body,
            verify=False,
        )
        handle_api_response_errors(response)
        return response.json()

    def execute_pre_setup_provider(self, inputs: Inputs):
        #  Ignored due to not needing to perform even a step before the clone
        pass

    def execute_repo_creation(self, inputs: Inputs):
        url_builder = (
            UrlBuilder(inputs).path("orgs").path(inputs.org_name).path("repos")
        )
        body = {
            "name": f"{inputs.repo_name}",
            "description": "StackSpot Workflows",
            "homepage": "https://stackspot.com",
            "private": True,
        }
        self.__post(url_builder, inputs, body)

    def repo_exists(self, inputs: Inputs) -> bool:
        try:
            self.__repo_info(inputs)
            return True
        except NotFoundError:
            return False
        except:
            raise

    def clone_url(self, inputs: Inputs) -> str:
        return f"https://git:{inputs.pat}@github.com/{inputs.org_name}/{inputs.repo_name}.git"

    def execute_provider_setup(self, inputs: Inputs):
        logging.info("Setting up repository webhook...")
        callback_url = "https://workflow-api.v1.stackspot.com/workflows/github/callback"
        url_builder = (
            UrlBuilder(inputs)
            .path("repos")
            .path(inputs.org_name)
            .path(inputs.repo_name)
            .path("hooks")
        )
        body = {
            "name": "web",
            "active": True,
            "events": ["workflow_job", "workflow_run"],
            "config": {
                "url": callback_url,
                "content_type": "json",
                "insecure_ssl": "0",
            },
        }
        self.__post(url_builder, inputs, body)
