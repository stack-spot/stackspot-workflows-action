import requests

from provider import Inputs
from provider.errors import NotFoundError
from provider.services.bitbucket.bitbucket_http import get, get_api_projects_builder, post, get_api_project_builder


class BitbucketCreateRepoException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ProjectNameTooShort(BitbucketCreateRepoException):
    def __init__(self, project_name):
        super().__init__(
            f"The name {project_name} is too short. It must contain at least 3 characters."
        )


class GetProjectGeneralError(BitbucketCreateRepoException):
    def __init__(self, err):
        super().__init__(f"An error occurred while listing the projects: {err}")


class CouldNotSetProjectKeyError(BitbucketCreateRepoException):
    def __init__(self):
        super().__init__(
            "Action was not able to set a project key based on the project name, please select a different project name."  # noqa E501
        )


class GetProjectKeyGeneralError(BitbucketCreateRepoException):
    def __init__(self, err):
        super().__init__(f"An error occurred while fetching the project keys: {err}")


def get_project_key_by_project_name(bitbucket_access_token: str, inputs: Inputs):
    project_key = __project_exists(bitbucket_access_token, inputs)
    if project_key:
        return project_key

    return __create_project(bitbucket_access_token, inputs)


def __project_exists(bitbucket_access_token: str, inputs: Inputs):
    try:
        data = get(get_api_projects_builder(inputs), bitbucket_access_token)
        values = data.get("values", [])
        project_exists = [
            val
            for val in values
            if val.get("key") == inputs.project_name or val.get("name") == inputs.project_name
        ]
        if project_exists:
            print(
                f"> Project '{inputs.project_name}' project found in the workspace {inputs.org_name}."
            )
            project = project_exists.pop()
            return project.get("key")
    except NotFoundError:
        print(f"> Project '{inputs.project_name}' not found in the workspace {inputs.org_name}.")
        return None
    except requests.exceptions.HTTPError as e:
        raise GetProjectGeneralError(e)


def __create_project(bitbucket_access_token: str, inputs: Inputs):
    print(
        f"> Creating project '{inputs.project_name}' in the workspace {inputs.org_name}."
    )

    if len(inputs.project_name) < 3:
        raise ProjectNameTooShort(inputs.project_name)

    cleaned_project_name = (
        inputs.project_name.replace(" ", "").replace("_", "").replace("-", "").upper()
    )

    maximum_name_length = len(cleaned_project_name) - 4
    key = cleaned_project_name[:3]
    if __project_key_exists(bitbucket_access_token, inputs, key):
        for i in range(maximum_name_length):
            key = cleaned_project_name[i + 1: i + 4]
            if i < maximum_name_length and __project_key_exists(bitbucket_access_token, inputs, key):
                continue
            elif i > maximum_name_length:
                raise CouldNotSetProjectKeyError()
            else:
                break

    print(f"> Project key set to {key}")

    payload = {"name": inputs.project_name, "key": key}
    post(get_api_projects_builder(inputs), bitbucket_access_token, payload)

    print(f"> Project '{inputs.project_name}' created in the workspace {inputs.org_name}.")

    return key


def __project_key_exists(bitbucket_access_token: str, inputs: Inputs, key: str):
    """
    Checks if the project key exists
    """
    print(f"> Checking if the '{key}' exists.")

    try:
        get(get_api_project_builder(inputs, key), bitbucket_access_token)
        return True
    except NotFoundError:
        print("> Key does not exists")
        return False
    except requests.exceptions.HTTPError as e:
        raise GetProjectKeyGeneralError(e)
