import requests

from provider.services.bitbucket.bitbucket_http import get, post
from provider.services.bitbucket.repository_pipeline_settings import create_or_update_repository_variables, \
    enable_repository_pipelines
from provider.services.bitbucket.bitbucket_http import get_api_base_url_builder
from .errors import NotFoundError
from .handle_errors import handle_api_response_errors
from .provider import Provider, Inputs


class BitBucketProvider(Provider):
    def __init__(self):
        self.bitbucket_access_token = None

    def __repo_info(self, inputs: Inputs) -> dict:
        return get(get_api_base_url_builder(inputs), self.bitbucket_access_token)

    def execute_provider_setup(self, inputs: Inputs):
        enable_repository_pipelines(inputs, self.bitbucket_access_token)
        create_or_update_repository_variables(inputs, self.bitbucket_access_token)

    def execute_repo_creation(self, inputs: Inputs):
        body = {
            "scm": "git",
            "is_private": True,
            "project": {"key": inputs.project_name},
        }
        post(get_api_base_url_builder(inputs), self.bitbucket_access_token, body)

    def repo_exists(self, inputs: Inputs) -> bool:
        try:
            self.__repo_info(inputs)
            return True
        except NotFoundError:
            return False

    def clone_url(self, inputs: Inputs) -> str:
        return f"https://x-token-auth:{self.bitbucket_access_token}@bitbucket.org/{inputs.org_name}/{inputs.repo_name}.git"  # noqa E501

    def execute_pre_setup_provider(self, inputs: Inputs):
        self.__login_with_client_credentials(inputs)

    def __login_with_client_credentials(self, inputs: Inputs):
        response = requests.post(
            url="https://bitbucket.org/site/oauth2/access_token",
            data={'grant_type': 'client_credentials'},
            auth=(inputs.client_key, inputs.client_secret)
        )
        handle_api_response_errors(response)
        response_json = response.json()
        self.bitbucket_access_token = response_json["access_token"]
