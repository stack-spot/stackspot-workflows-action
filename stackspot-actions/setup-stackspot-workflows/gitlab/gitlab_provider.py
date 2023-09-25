import logging

from http_client import HttpClient
from provider import Provider
from gitlab.gitlab_inputs import GitlabInputs
from gitlab.gitlab_api_client import GitlabApiClient


class GitlabProvider(Provider):

    def __init__(self, http_client: HttpClient, **kwargs):
        super().__init__()
        self.inputs: GitlabInputs = GitlabInputs(repo_name=kwargs.get("project_name"), **kwargs)
        self.api = GitlabApiClient(http_client=http_client, pat=self.inputs.pat)
        self.project_id = ""
        self.trigger_id = ""
        self.http_url_to_repo = ""

    def execute_pre_setup_provider(self):
        pass

    def execute_provider_setup(self):
        response = self.api.create_trigger(project_id=self.project_id)
        if response.ok:
            self.trigger_id = response.json()["id"]
            return
        logging.info("Failure creating trigger")
        response.raise_for_status()

    def execute_repo_creation(self):
        response = self.api.create_project(project_name=self.inputs.project_name)
        if response.ok:
            self.project_id = response.json()["id"]
            self.http_url_to_repo = response.json()["http_url_to_repo"]
            return
        logging.info("Failure creating gitlab repository")
        response.raise_for_status()

    def repo_exists(self) -> bool:
        response = self.api.get_project(group_name=self.inputs.group_name, project_name=self.inputs.project_name)
        print(response.json())
        if response.ok:
            self.project_id = response.json()["id"]
            self.http_url_to_repo = response.json()["http_url_to_repo"]
            return True
        elif response.status_code == 404:
            return False
        logging.info("Failure getting gitlab project")
        response.raise_for_status()

    def clone_url(self) -> str:
        return self.http_url_to_repo.replace("https://gitlab.com/", f"https://x-token-auth:{self.inputs.pat}@gitlab.com/")

    def create_pull_request(self):
        response = self.api.create_merge_request(
            project_id=self.project_id,
            pr_title=self.inputs.pr_title,
            pr_description=self.inputs.pr_title,
            source_branch=self.inputs.ref_branch,
            target_branch="main",
        )
        if response.ok:
            return
        logging.info("Failure creating gitlab merge request")
        response.raise_for_status()

    @property
    def scm_config_url(self) -> str:
        return f"https://gitlab.com/{self.inputs.group_name}/{self.inputs.project_name}?project_id={self.project_id}&trigger_id={self.trigger_id}"
