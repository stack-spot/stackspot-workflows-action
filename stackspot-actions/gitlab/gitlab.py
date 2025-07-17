import requests
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger()

class GroupNotFound(Exception):
    def __init__(self, group_name: str):
        super().__init__(f"Group {group_name} not found!")

class GitlabCreateRepository:
    CONFLICT = {
        'message': {
            'project_namespace.name': ['has already been taken'],
            'name': ['has already been taken'],
            'path': ['has already been taken']
        }
    }

    def __init__(self, token: str, **_) -> None:
        self.base_url = "https://gitlab.com"
        self.headers = {"Private-Token": token, "Content-Type": "application/json"}

    def __call__(self, group_name: str, name: str, visibility: str, subgroup: Optional[str] = None, **_) -> Any:
        # Get the group or subgroup
        group = self.get_group(group_name, subgroup)
        if not group:
            raise GroupNotFound(group_name=group_name)

        # Create the project under the group or subgroup
        repository = self.create_project(namespace_id=group["id"], name=name, visibility=visibility)
        return repository.get("http_url_to_repo", f"https://gitlab.com/{group['path']}/{name}.git")

    def get_group(self, group_name: str, subgroup: Optional[str] = None) -> Optional[Dict]:
        logger.info(f"Getting group '{group_name}' ...")
        url = f"{self.base_url}/api/v4/groups"
        response = requests.get(url, headers=self.headers, params=dict(search=group_name))
        response.raise_for_status()
        groups = response.json()

        # Find the main group
        for group in groups:
            if group['name'] == group_name:
                # If subgroup is provided, search for it within the group
                if subgroup:
                    return self.get_subgroup(group['id'], subgroup)
                return group

    def get_subgroup(self, group_id: int, subgroup_name: str) -> Optional[Dict]:
        logger.info(f"Getting subgroup '{subgroup_name}' under group ID '{group_id}' ...")
        url = f"{self.base_url}/api/v4/groups/{group_id}/subgroups"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        subgroups = response.json()

        # Find the subgroup
        for subgroup in subgroups:
            if subgroup['name'] == subgroup_name:
                return subgroup

        logger.error(f"Subgroup '{subgroup_name}' not found under group ID '{group_id}'")
        return None

    def create_project(self, **data) -> Optional[Dict]:
        logger.info(f"Creating project '{data.get('name')}' ...")
        url = f"{self.base_url}/api/v4/projects"
        response = requests.post(url, json=data, headers=self.headers)
        if response.ok:
            return response.json()
        if response.status_code == 400 and response.json() == self.CONFLICT:
            return dict()
        response.raise_for_status()