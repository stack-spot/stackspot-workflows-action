import requests
import logging
from .errors import NotFoundError
from .provider import Provider, Inputs

APPLICATION_JSON = "application/json"


class UrlBuilder:
    def __init__(self, inputs: Inputs):
        self.inputs = inputs
        self.base_url = "https://api.bitbucket.org/2.0"
        self.paths = []

    def path(self, path: str) -> "UrlBuilder":
        self.paths.append(path)
        return self

    def build(self) -> str:
        return "/".join([self.base_url, *self.paths])


class PipelineVariable:
    def __init__(self, key: str, value: str, secured=False):
        self.key = key
        self.value = value
        self.secured = secured


class BitBucketProvider(Provider):
    def __init__(self):
        self.bitbucket_access_token = None
        self.__pipeline_variables = [
            PipelineVariable("workflow_config", "stk"),
            PipelineVariable("debug", "false"),
            PipelineVariable("debugHttp", "false"),
            PipelineVariable("workflow_api", "https://workflow-api.v1.stackspot.com")
        ]

    def __default_headers(self):
        return {
            "Authorization": f"Bearer {self.bitbucket_access_token}",
            "Accept": APPLICATION_JSON,
        }

    def __default_post_headers(self):
        post_headers = {"Content-Type": APPLICATION_JSON}
        post_headers.update(self.__default_headers())
        return post_headers

    def __get_api_base_url_builder(self, inputs: Inputs) -> UrlBuilder:
        return UrlBuilder(inputs).path("repositories").path(inputs.org_name).path(inputs.repo_name)

    def __get_api_pipeline_config_url_builder(self, inputs: Inputs) -> UrlBuilder:
        return self.__get_api_base_url_builder(inputs).path("pipelines_config")

    def __get_api_pipeline_config_variables_url_builder(self, inputs: Inputs) -> UrlBuilder:
        return self.__get_api_pipeline_config_url_builder(inputs).path("variables")

    def __repo_info(self, inputs: Inputs) -> dict:
        return self.__get(self.__get_api_base_url_builder(inputs))

    def __get(self, url_builder: UrlBuilder) -> dict:
        response = requests.get(
            url_builder.build(),
            headers=self.__default_headers(),
        )
        self._handle_api_response_errors(response)
        return response.json()

    def __post(self, url_builder: UrlBuilder, body: dict) -> dict:
        response = requests.post(
            url_builder.build(),
            headers=self.__default_post_headers(),
            json=body,
        )
        self._handle_api_response_errors(response)
        return response.json()

    def __put(self, url_builder: UrlBuilder, body: dict) -> dict:
        response = requests.put(
            url_builder.build(),
            headers=self.__default_post_headers(),
            json=body,
        )
        self._handle_api_response_errors(response)
        return response.json()

    def execute_provider_setup(self, inputs: Inputs):
        self.__enable_repository_pipelines(inputs)
        self.__create_or_update_repository_variables(inputs)

    def execute_repo_creation(self, inputs: Inputs):
        body = {
            "scm": "git",
            "is_private": True,
            "project": {"key": inputs.project_name},
        }
        self.__post(self.__get_api_base_url_builder(inputs), body)

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

    def __enable_repository_pipelines(self, inputs: Inputs):
        print()
        logging.info(f"Enabling pipelines of repository {inputs.repo_name}")
        body = {"enabled": True}
        self.__put(self.__get_api_pipeline_config_url_builder(inputs), body)

    def __login_with_client_credentials(self, inputs: Inputs):
        response = requests.post(
            url="https://bitbucket.org/site/oauth2/access_token",
            data={'grant_type': 'client_credentials'},
            auth=(inputs.client_key, inputs.client_secret)
        )
        self._handle_api_response_errors(response)
        response_json = response.json()
        self.bitbucket_access_token = response_json["access_token"]

    def __create_or_update_repository_variables(self, inputs: Inputs):
        if inputs.create_repo:
            self.__create_repository_variables(inputs)
            return

        repository_variables = self.__get_repository_variables(inputs)

        for pipeline_variable in self.__pipeline_variables:
            existing_pipeline_variable = [x for x in repository_variables["values"]
                                          if pipeline_variable.key == x["key"]]
            if existing_pipeline_variable:
                existing_pipeline_variable = existing_pipeline_variable.pop()
                if pipeline_variable.value != existing_pipeline_variable["value"]:
                    self.__update_repository_variable(inputs, pipeline_variable, existing_pipeline_variable["uuid"])
                else:
                    logging.info(f"Repository Variable Already Updated '{pipeline_variable.key}'")
                continue

            self.__create_repository_variable(inputs, pipeline_variable)

    def __get_repository_variables(self, inputs: Inputs):
        return self.__get(self.__get_api_pipeline_config_variables_url_builder(inputs))

    def __create_repository_variables(self, inputs):
        for pipeline_variable in self.__pipeline_variables:
            self.__create_repository_variable(inputs, pipeline_variable)

    def __create_repository_variable(self, inputs: Inputs, pipeline_variable: PipelineVariable):
        logging.info(f"Creating Repository Variable '{pipeline_variable.key}'")

        body = {
            "type": "pipeline_variable",
            "key": pipeline_variable.key,
            "value": pipeline_variable.value,
            "secured": pipeline_variable.secured
        }
        self.__post(self.__get_api_pipeline_config_variables_url_builder(inputs), body)

    def __update_repository_variable(self, inputs: Inputs, pipeline_variable: PipelineVariable, pipeline_variable_id):
        logging.info(f"Updating Repository Variable '{pipeline_variable.key}'")
        url_builder = self.__get_api_pipeline_config_variables_url_builder(inputs).path(pipeline_variable_id)
        body = {
            "value": pipeline_variable.value,
            "secured": pipeline_variable.secured
        }
        self.__put(url_builder, body)
