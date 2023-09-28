import logging

from helpers.git_helper import Git
from helpers.http_client import HttpClient
from helpers.stk import Stk
from bitbucket.bitbucket_api_client import BitbucketApiClient
from bitbucket.bitbucket_inputs import BitbucketInputs
from provider import Provider


class BitbucketProvider(Provider):
    def __init__(self, stk: Stk, git: Git, http_client: HttpClient, **kwargs):
        super().__init__(stk=stk, git=git)
        self.inputs: BitbucketInputs = BitbucketInputs(**kwargs)
        self.api = BitbucketApiClient(
            http_client=http_client,
            client_key=self.inputs.client_key,
            client_secret=self.inputs.client_secret
        )
        self.bitbucket_access_token = None
        self.project_key = None

    def _project_exists(self):
        response = self.api.get_projects(
            workspace_name=self.inputs.workspace_name,
            project_name=self.inputs.project_name
        )
        self.project_key = response.json().get("key")

    def extra_setup(self):
        self.api.update_repository_pipeline(
            workspace_name=self.inputs.workspace_name,
            repository_name=self.inputs.repo_name
        )

    def execute_repo_creation(self):
        self._project_exists()
        self.api.create_repository(
            workspace_name=self.inputs.workspace_name,
            repository_name=self.inputs.repo_name,
            project_key=self.project_key,
        )

    def repo_exists(self) -> bool:
        response = self.api.get_repository(
            workspace_name=self.inputs.workspace_name,
            repository_name=self.inputs.repo_name,
            raise_for_status=False,
        )
        if response.ok:
            return True
        elif response.status_code == 404:
            return False
        logging.info("Failure getting bitbucket repository!")
        response.raise_for_status()

    @property
    def clone_url(self) -> str:
        return f"https://x-token-auth:{self.api.authorization}@bitbucket.org/{self.inputs.workspace_name}/{self.inputs.repo_name}.git"  # noqa E501

    def create_pull_request(self):
        response = self.api.create_pull_request(
            workspace_name=self.inputs.workspace_name,
            repository_name=self.inputs.repo_name,
            pr_title=self.inputs.pr_title,
            pr_source=self.inputs.ref_branch,
            pr_destination="main"
        )
        return response.json()['links']['html']['href']

    @property
    def scm_config_url(self) -> str:
        return f""
