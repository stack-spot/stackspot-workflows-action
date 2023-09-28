import logging

from provider import Inputs
from provider.services.bitbucket.bitbucket_http import post, get, get_api_pipeline_config_variables_url_builder, put, \
    get_api_pipeline_config_url_builder
from provider.services.bitbucket.models import PipelineVariable

PIPELINE_VARIABLES = [
    PipelineVariable("workflow_config", "stk"),
    PipelineVariable("debug", "false"),
    PipelineVariable("debugHttp", "false"),
    PipelineVariable("workflow_api", "https://workflow-api.v1.stackspot.com")
]


def __create_repository_variable(bitbucket_access_token: str, inputs: Inputs, pipeline_variable: PipelineVariable):
    logging.info(f"Creating Repository Variable '{pipeline_variable.key}'")

    body = {
        "type": "pipeline_variable",
        "key": pipeline_variable.key,
        "value": pipeline_variable.value,
        "secured": pipeline_variable.secured
    }
    post(get_api_pipeline_config_variables_url_builder(inputs), bitbucket_access_token, body)


def __get_repository_variables(bitbucket_access_token: str, inputs: Inputs):
    return get(get_api_pipeline_config_variables_url_builder(inputs), bitbucket_access_token)


def __update_repository_variable(bitbucket_access_token: str, inputs: Inputs, pipeline_variable: PipelineVariable,
                                 pipeline_variable_id):
    logging.info(f"Updating Repository Variable '{pipeline_variable.key}'")
    url_builder = get_api_pipeline_config_variables_url_builder(inputs).path(pipeline_variable_id)
    body = {
        "value": pipeline_variable.value,
        "secured": pipeline_variable.secured
    }
    put(url_builder, bitbucket_access_token, body)
