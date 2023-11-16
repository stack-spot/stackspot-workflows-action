import logging

from helpers.git_helper import Git
from helpers.http_client import HttpClient
from provider import Provider
from azure.azure_inputs import AzureInputs
from azure.azure_api_client import AzureApiClient
from helpers.stk import Stk


class AzureProvider(Provider):
    PIPELINE_NAME = "middle-flow"
    clone_url_mask = "https://{org_name}:{pat}@dev.azure.com/{org_name}/{project_name}/_git/{repository_name}"

    def __init__(self, stk: Stk, git: Git, http_client: HttpClient, **kwargs):
        super().__init__(stk=stk, git=git)
        self.inputs: AzureInputs = AzureInputs(repo_name=kwargs.get("project_name"), **kwargs)
        self.api = AzureApiClient(http_client=http_client, pat=self.inputs.pat)

    @property
    def repository_id(self):
        response = self.api.get_repository(
            org_name=self.inputs.org_name,
            project_name=self.inputs.project_name,
            repository_name=self.inputs.project_name,
        )
        return response.json()["id"]

    @property
    def project_id(self) -> str:
        response = self.api.get_project(org_name=self.inputs.org_name, project_name=self.inputs.project_name)
        return response.json()["id"]

    def create_pull_request(self) -> str:
        response = self.api.create_pull_request(
            org_name=self.inputs.org_name,
            respository_name=self.inputs.repo_name,
            project_name=self.inputs.project_name,
            pr_title=self.inputs.pr_title,
            pr_description=self.inputs.pr_title,
            pr_source=self.inputs.ref_branch,
            pr_target="main"
        )
        pr_mask = "https://dev.azure.com/{org_name}/{project_name}/_git/{repo_name}/pullrequest/{pr_id}"
        return pr_mask.format(
            org_name=self.inputs.org_name,
            project_name=self.inputs.project_name,
            repo_name=self.inputs.repo_name,
            pr_id=response.json()["pullRequestId"]
        )

    def execute_repo_creation(self):
        self.api.create_project(
            org_name=self.inputs.org_name,
            project_name=self.inputs.project_name,
        )

    def repo_exists(self) -> bool:
        response = self.api.get_project(org_name=self.inputs.org_name, project_name=self.inputs.project_name, raise_for_status=False)
        if response.ok:
            return True
        elif response.status_code == 404:
            return False
        logging.info(f"Failure getting azure project: {self.inputs.org_name}/{self.inputs.project_name}")
        response.raise_for_status()

    @property
    def clone_url(self) -> str:
        return self.clone_url_mask.format(
            org_name=self.inputs.org_name,
            pat=self.inputs.pat,
            project_name=self.inputs.project_name,
            repository_name=self.inputs.project_name,
        )

    def _create_pipeline(self):
        response = self.api.create_pipeline(
            org_name=self.inputs.org_name,
            project_name=self.inputs.project_name,
            repository_id=self.repository_id,
            pipeline_name=self.PIPELINE_NAME,
            raise_for_status=False
        )
        if response.ok:
            return
        elif response.status_code == 409:
            logging.info(f"Pipeline {self.PIPELINE_NAME} already exists")
            return
        response.raise_for_status()

    def extra_setup(self):
        self._create_pipeline()

    @property
    def scm_config_url(self) -> str:
        return f"https://dev.azure.com/{self.inputs.org_name}/{self.inputs.project_name}"
