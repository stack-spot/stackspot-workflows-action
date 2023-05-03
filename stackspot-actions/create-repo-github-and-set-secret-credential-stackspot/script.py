import requests
import json
import re
from base64 import b64encode
from nacl import encoding, public

API_BASE_URL = "https://api.github.com"
JWT_REGEX=r"^([a-zA-Z0-9_=]+)\.([a-zA-Z0-9_=]+)\.([a-zA-Z0-9_\-\+\/=]*)"

def run(metadata):
    inputs = metadata.inputs
    org = inputs.get("org")
    visibility = inputs.get("visibility")
    token = inputs.get("token")
    repo_name = inputs.get("name")
    client_id = inputs.get("client_id")
    client_key = inputs.get("client_key")
    client_realm = inputs.get("client_realm")

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
        "name": repo_name,
        "description": inputs.get('description'),
        "private": private,
        "visibility": visibility,
        "auto_init": True
    }

    # Create Repo
    is_jwt = re.search(JWT_REGEX, token)
    headers = {
        "Authorization": f"{'Bearer' if is_jwt else 'token'} {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    r = requests.post(f"{API_BASE_URL}/orgs/{org}/repos", headers=headers, json=data, verify=False)
    response = r.json()

    print(f"Success created repository {response.get('html_url')}")

    set_secret('STK_CLIENT_ID', client_id, org, repo_name, token)
    set_secret('STK_CLIENT_KEY', client_key, org, repo_name, token)
    set_secret('STK_CLIENT_REALM', client_realm, org, repo_name, token)

    print("Secrets Created on Repo!")

def set_secret(secret_name, secret_value, org, repo, token):
    is_jwt = re.search(JWT_REGEX, token)
    headers = {
        "Authorization": f"{'Bearer' if is_jwt else 'token'} {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    repo_key = get_repo_key(org, repo, token)
    secret_encrypted = encrypt(repo_key.get('key'), secret_value)
    key_id = repo_key.get('key_id')

    data = {
        "encrypted_value": secret_encrypted,
        "key_id": key_id
    }
    url = f"{API_BASE_URL}/repos/{org}/{repo}/actions/secrets/{secret_name}"
    r = requests.put(url, headers=headers, json=data, verify=False)
    r.raise_for_status()

    print(f"Secret {secret_name} created!")

def get_repo_key(org, repo, token):
    is_jwt = re.search(JWT_REGEX, token)
    headers = {
        "Authorization": f"{'Bearer' if is_jwt else 'token'} {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"{API_BASE_URL}/repos/{org}/{repo}/actions/secrets/public-key"
    r = requests.get(url, headers=headers, verify=False)
    r.raise_for_status()
    response = r.json()
    return response

def encrypt(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")