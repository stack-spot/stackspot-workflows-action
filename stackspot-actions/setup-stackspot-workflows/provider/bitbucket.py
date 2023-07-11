import logging
import requests

from provider.services.bitbucket.bitbucket_http import (
    get,
    get_api_pullrequests_url_builder,
    post,
)
from provider.services.bitbucket.repository_pipeline_settings import (
    create_or_update_repository_variables,
    enable_repository_pipelines,
)
from provider.services.bitbucket.bitbucket_http import get_api_base_url_builder
from .errors import NotFoundError
from .handle_errors import handle_api_response_errors
from .provider import Provider, Inputs
from .services.bitbucket.project_create import get_project_key_by_project_name


class BitBucketProvider(Provider):
    def __init__(self):
        self.bitbucket_access_token = None
        self.project_key = None

    def __repo_info(self, inputs: Inputs) -> dict:
        return get(get_api_base_url_builder(inputs), self.bitbucket_access_token)

    def execute_pre_setup_provider(self, inputs: Inputs):
        self.__login_with_client_credentials(inputs)
        self.project_key = get_project_key_by_project_name(
            self.bitbucket_access_token, inputs
        )

    def execute_provider_setup(self, inputs: Inputs):
        enable_repository_pipelines(inputs, self.bitbucket_access_token)
        create_or_update_repository_variables(inputs, self.bitbucket_access_token)
        print(
            f"\nSetup configured successfully on repository: {self.get_repository_url(inputs)}"
        )

    def execute_repo_creation(self, inputs: Inputs):
        body = {
            "scm": "git",
            "is_private": True,
            "project": {"key": self.project_key},
        }
        post(get_api_base_url_builder(inputs), self.bitbucket_access_token, body)

    def repo_exists(self, inputs: Inputs) -> bool:
        try:
            self.__repo_info(inputs)
            return True
        except NotFoundError:
            return False

    def get_repository_url(self, inputs: Inputs) -> str:
        return (
            f"https://bitbucket.org/{inputs.org_name}/{inputs.repo_name}"  # noqa E501
        )

    def clone_url(self, inputs: Inputs) -> str:
        return f"https://x-token-auth:{self.bitbucket_access_token}@bitbucket.org/{inputs.org_name}/{inputs.repo_name}.git"  # noqa E501

    def create_pull_request(self, inputs: Inputs) -> str:
        logging.info(f"Creating pull request from {inputs.ref_branch} to main brancn.")
        body = {
            "title": "Stackspot Update workflow configuration.",
            "source": {"branch": {"name": inputs.ref_branch}},
            "destination": {"branch": {"name": "main"}},
        }
        response = post(
            get_api_pullrequests_url_builder(inputs), self.bitbucket_access_token, body
        )

        if response and "links" in response:
            logging.info(
                f"Pull request created at: {response['links']['html']['href']}"
            )

    def __login_with_client_credentials(self, inputs: Inputs):
        response = requests.post(
            url="https://bitbucket.org/site/oauth2/access_token",
            data={"grant_type": "client_credentials"},
            auth=(inputs.client_key, inputs.client_secret),
        )
        handle_api_response_errors(response)
        response_json = response.json()
        self.bitbucket_access_token = response_json["access_token"]
