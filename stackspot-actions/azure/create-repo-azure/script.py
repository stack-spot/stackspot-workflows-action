import requests
import time
import base64

def get_projectid_by_name(project_name):
    """
    Searches the project id by name
    Returns the id if found, 'None' if not
    """
    url = f"{base_url}/_apis/projects/{project_name}?api-version=7.0"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("id")
    if response.status_code == 404:
        return None
    response.raise_for_status()

def project_exists(project_name):
    """
    Checks if a project exists in Azure DevOps with the specified name.
    Returns True if the project exists and False otherwise.
    """
    print(f"> Checking if the '{project_name}' project exists in your organization.")

    project_id = get_projectid_by_name(project_name)

    if project_id is not None:
        print(f"The project already exists.")
        return True
    
    print(f"The project does not exist.")
    return False

def create_project(project_name):
    """
    Creates a new project in Azure DevOps with the specified name.
    Waits for the project creation to finish before returning.
    """
    print(f"> Creating the '{project_name}' project.")

    url = f"{base_url}/_apis/projects?api-version=7.0"
    data = {
        "name": project_name,
        "capabilities": {
            "versioncontrol": {
                "sourceControlType": "Git"
            },
            "processTemplate": {
                "templateTypeId": "6b724908-ef14-45cf-84f8-768b5384da45"
            }
        }
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 202:
        url = response.json().get("url")
        for i in range(15):
            print(f"Waiting to finalize the provisioning...")
            time.sleep(5)
            response_check = requests.get(url, headers=headers)
            status = response_check.json().get("status")
            if status in ["provisioning", "inProgress"]:
                continue
            if status == "succeeded":
                print(f"The {project_name} project successfully created.")
                return
            else:
                raise Exception(f"Error: Failed to create '{project_name}' project. Status: {status}")
        raise Exception(f"Error: Failed to create '{project_name}' project. Time out.")
    else:
        response.raise_for_status()

def repository_exists(project_name, repo_name):
    """
    Checks if a repository exists in an Azure DevOps project with the specified name.
    Returns True if the repository exists and False otherwise.
    """
    print(f"> Checking if the '{repo_name}' repository exists in your project")
    
    url = f"{base_url}/{project_name}/_apis/git/repositories/{repo_name}?api-version=4.1"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(f"The repository already exists.")
        repo = response.json().get("remoteUrl")
        print(f"Exporting to pipeline git url variable...")
        print(f"##vso[task.setvariable variable=create_repo;]{repo}")
        return True
    elif response.status_code == 404:
        print(f"The repository does not exist.")
        return False
    response.raise_for_status()

def create_repository(project_name, repo_name):
    """
    Creates a new repository in an Azure DevOps project with the specified name.
    Waits for the repository creation to finish before returning.
    """
    print(f"> Creating the '{repo_name}' repository in '{project_name}' project.")

    url = f"{base_url}/{project_name}/_apis/git/repositories?api-version=7.0"
    data = {
        "name": repo_name,
        "project": {
            "id": get_projectid_by_name(project_name)
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        repo_url=response.json().get("remoteUrl")
        print(f"The {repo_name} repository successfully created.\n{repo_url}")
        print(f"Exporting to pipeline git url variable...")
        print(f"##vso[task.setvariable variable=create_repo;]{repo_url}")
        return
    raise Exception(f"Error: Failed to create {repo_name} repository. {response.text}")

def run(metadata):
    global base_url
    global headers
    inputs = metadata.inputs

    auth = base64.b64encode(f":{inputs.get('token')}".encode()).decode()
    base_url = f"https://dev.azure.com/{inputs.get('org')}"
    headers = {"Authorization": f"Basic {auth}"}

    project_name = inputs.get("project_key")
    repo_name = inputs.get("name")

    if not project_exists(project_name):
        create_project(project_name)
        
    if not repository_exists(project_name, repo_name):
        create_repository(project_name, repo_name)