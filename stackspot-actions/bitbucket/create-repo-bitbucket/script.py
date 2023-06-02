import json
import requests


class Exceptions(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    @classmethod
    def workspace_not_found(cls, workspace):
        return cls(f"The {workspace} workspace was not found.")

    @classmethod
    def project_name_to_short(cls, project_name):
        return cls(
            f"The name {project_name} is too short. It must contain at least 3 characters."
        )

    @classmethod
    def project_creation_error(cls, err):
        return cls(f"An error ocurred while creating the project: {err}")

    @classmethod
    def repository_exists_general_error(cls, err):
        return cls(f"An error ocurred while checking if the repository exists: {err}")

    @classmethod
    def workspace_exists_general_error(cls, err):
        return cls(f"An error ocurred while checking if the workspace exists: {err}")

    @classmethod
    def create_repository_error(cls, err):
        return cls(f"An error ocurred while creating the repository: {err}")


def __workspace_exists(workspace_name: str):
    """
    Checks if the workspace exists
    Workspaces can not be created by API integration
    """
    print(
        f"> Checking if the '{workspace_name}' workspace exists in your organization."
    )

    url = f"{base_url}/workspaces/{workspace_name}/permissions"

    try:
        response = requests.get(url, headers=get_headers)
        response.raise_for_status()
        print(f"> Workspace '{workspace_name}' found.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in (
            requests.codes.not_found,
            requests.codes.forbidden,
            requests.codes.unauthorized,
        ):
            raise Exceptions.workspace_not_found(workspace_name)
        raise Exceptions.workspace_exists_general_error(e)


def __repository_exists(workspace_name: str, repo_name: str):
    """
    Checks if the repository exists
    """
    print(
        f"> Checking if the '{repo_name}' repository exists in the workspace {workspace_name}."
    )

    url = f"{base_url}/repositories/{workspace_name}/{repo_name}"

    try:
        response = requests.get(url, headers=get_headers)
        response.raise_for_status()
        print(f">'{repo_name}' already exists.")
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == requests.codes.not_found:
            print(f">'{repo_name}' not found. It will be created.")
            return False
        raise Exceptions.repository_exists_general_error(e)


def __project_exists(workspace_name: str, project_name: str):
    """
    Checks if the informed project exists
    """
    print(
        f"> Checking if the '{project_name}' project exists in the workspace {workspace_name}."
    )
    url = f"{base_url}/workspaces/{workspace_name}/projects"

    try:
        response = requests.get(url, get_headers)
        response.raise_for_status()
        data = response.json()
        values = data.get("values", [])
        project_exists = [
            val
            for val in values
            if val.get("key") == project_name or val.get("name") == project_name
        ]
        if project_exists:
            print(
                f"> Project '{project_name}' project found in the workspace {workspace_name}."
            )
            project = project_exists.pop()
            return project.get("key")
    except requests.exceptions.HTTPError as e:
        print(
            f"> Project '{project_name}' not found in the workspace {workspace_name}."
        )
        if e.response.status_code == requests.codes.not_found:
            return None


def __create_project(workspace_name: str, project_name: str):
    """
    Creates a new Bitbucket Project in the workspace
    """
    print(f"> Creating project '{project_name}' in the workspace {workspace_name}.")
    url = f"{base_url}/workspaces/{workspace_name}/projects"

    if len(project_name) < 3:
        raise Exceptions.project_name_to_short(project_name)

    key = project_name.replace(" ", "").replace("_", "").replace("-", "")[:3].upper()
    print(f"> Project key set to {key}")

    payload = json.dumps({"name": project_name, "key": key})

    try:
        response = requests.post(url, headers=post_headers, data=payload)
        response.raise_for_status()
        print(f"> Project '{project_name}' created in the workspace {workspace_name}.")
    except requests.exceptions.HTTPError as e:
        raise Exceptions.project_creation_error(e)

    return key


def __create_repository(workspace_name: str, project_key: str, repo_name: str):
    """
    Creates a new repository on bitbucket
    """
    print(f"> Creating repository '{repo_name}' in the project {project_key}.")

    url = f"{base_url}/repositories/{workspace_name}/{repo_name}"

    payload = json.dumps({"scm": "git", "project": {"key": project_key}})

    try:
        response = requests.post(url, data=payload, headers=post_headers)
        response.raise_for_status()
        print(f"Repository {repo_name} successfully created.")
    except requests.exceptions.HTTPError as e:
        raise Exceptions.create_repository_error(e)


def run(metadata):
    global base_url
    global get_headers
    global post_headers
    base_url = "https://api.bitbucket.org/2.0"
    inputs = metadata.inputs
    token = inputs.get("token")
    get_headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    post_headers = {"Content-Type": "application/json"}
    post_headers.update(get_headers)

    workspace_name = inputs.get("workspace_name")
    project_name = inputs.get("project_name")
    repo_name = inputs.get("repo_name")

    __workspace_exists(workspace_name)
    if not __repository_exists(workspace_name, repo_name):
        project_key = __project_exists(workspace_name, project_name)
        if not project_key:
            project_key = __create_project(workspace_name, project_name)
        __create_repository(workspace_name, project_key, repo_name)
