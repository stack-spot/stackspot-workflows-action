import requests

from provider import Inputs
from provider.services.bitbucket.models import UrlBuilder
from provider.handle_errors import handle_api_response_errors

APPLICATION_JSON = "application/json"


def __default_headers(bitbucket_access_token: str):
    return {
        "Authorization": f"Bearer {bitbucket_access_token}",
        "Accept": APPLICATION_JSON,
    }


def __default_post_headers(bitbucket_access_token: str):
    post_headers = {"Content-Type": APPLICATION_JSON}
    post_headers.update(__default_headers(bitbucket_access_token))
    return post_headers


def get_api_base_url_builder(inputs: Inputs) -> UrlBuilder:
    return UrlBuilder(inputs).path("repositories").path(inputs.org_name).path(inputs.repo_name)


def get_api_projects_builder(inputs: Inputs) -> UrlBuilder:
    return UrlBuilder(inputs).path("workspaces").path(inputs.org_name).path("projects")


def get_api_project_builder(inputs: Inputs, project_key: str) -> UrlBuilder:
    return get_api_projects_builder(inputs).path(project_key)


def get_api_pipeline_config_url_builder(inputs: Inputs) -> UrlBuilder:
    return get_api_base_url_builder(inputs).path("pipelines_config")


def get_api_pipeline_config_variables_url_builder(inputs: Inputs) -> UrlBuilder:
    return get_api_pipeline_config_url_builder(inputs).path("variables")


def get(url_builder: UrlBuilder, bitbucket_access_token) -> dict:
    response = requests.get(
        url_builder.build(),
        headers=__default_headers(bitbucket_access_token),
    )
    handle_api_response_errors(response)
    return response.json()


def post(url_builder: UrlBuilder, bitbucket_access_token, body: dict) -> dict:
    response = requests.post(
        url_builder.build(),
        headers=__default_post_headers(bitbucket_access_token),
        json=body,
    )
    handle_api_response_errors(response)
    return response.json()


def put(url_builder: UrlBuilder, bitbucket_access_token, body: dict) -> dict:
    response = requests.put(
        url_builder.build(),
        headers=__default_post_headers(bitbucket_access_token),
        json=body,
    )
    handle_api_response_errors(response)
    return response.json()
