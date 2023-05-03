import requests
import json
import re

API_BASE_URL = "https://api.github.com"
JWT_REGEX=r"^([a-zA-Z0-9_=]+)\.([a-zA-Z0-9_=]+)\.([a-zA-Z0-9_\-\+\/=]*)"

def format_data(inputs: dict, name_parameters: list):
    data = {}
    for parameter in name_parameters:
        if inputs.get(parameter) != None:
            data[parameter] = inputs.get(parameter)
    return data

def run(metadata):
    inputs = metadata.inputs
    org = inputs.get("org")
    visibility = inputs.get("visibility")

    if visibility == "internal":
        private = True
        visibility = "internal"
    elif visibility == "public":
        private = False
        visibility = "public"
    else:
        private = True
        visibility = "private"
        
    data = {
        "name": inputs.get("name"),
        "description": inputs.get('description'),
        "private": private,
        "visibility": visibility,
        "auto_init": True
    }

    is_jwt = re.search(JWT_REGEX, inputs.get('token'))
    headers = {
        "Authorization": f"{'Bearer' if is_jwt else 'token'} {inputs.get('token')}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    r = requests.post(f"{API_BASE_URL}/orgs/{org}/repos", headers=headers, json=data)
    response = r.json()

    if r.status_code == 403:
        output =  "Forbidden access, check your token value and try again"
        print(output)
        raise Exception(output)
    if r.status_code != 201:
        output = "Repository creation failed. Output detail:\n\n" + json.dumps(response)
        print(output)
        raise Exception(output)

    print(f"Success created repository {response.get('html_url')}")
