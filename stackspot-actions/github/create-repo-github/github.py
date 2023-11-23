import requests
import json
import re
import logging

logger = logging.getLogger()


class GithubCreateRepository:
    API_BASE_URL = "https://api.github.com"
    TOKEN_PATTERN = r"^([a-zA-Z0-9_=]+)\.([a-zA-Z0-9_=]+)\.([a-zA-Z0-9_\-\+\/=]*)"
    CONFLICT_ERROR = dict(
        resource="Repository",
        code="custom",
        field="name",
        message="name already exists on this account"
    )

    def __init__(self, org: str, token: str, **_):
        self.org = org
        is_jwt = re.search(self.TOKEN_PATTERN, token)
        self.api_headers = {
            "Authorization": f"{'Bearer' if is_jwt else 'token'} {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_repository(self, repository_name: str, repository_description: str, visibility: str):
        logger.info(f"Creating repository '{repository_name}' ...")
        url = f"{self.API_BASE_URL}/orgs/{self.org}/repos"
        data = {
            "name": repository_name,
            "description": repository_description,
            "private": visibility != "public",
            "visibility": visibility,
            "auto_init": True
        }
        response = requests.post(url, headers=self.api_headers, json=data)
        response_json = response.json()
        if response.ok or (response.status_code == 422 and response_json.get("errors") == [self.CONFLICT_ERROR]):
            return
        response.raise_for_status()

    def __call__(self, name: str, description: str, visibility: str, **_) -> str:
        self.create_repository(repository_name=name, repository_description=description, visibility=visibility)
        return f"https://github.com/{self.org}/{name}"
