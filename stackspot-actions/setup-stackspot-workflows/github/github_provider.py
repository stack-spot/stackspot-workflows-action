import logging

from helpers.git_helper import Git
from helpers.http_client import HttpClient
from helpers.stk import Stk
from provider import Provider
from github.github_api_client import GithubApiClient
from github.github_inputs import GithubInputs


class GithubProvider(Provider):
    clone_url_mask = "https://git:{pat}@github.com/{org_name}/{repo_name}.git"

    def __init__(self, stk: Stk, git: Git, http_client: HttpClient, **kwargs):
        super().__init__(stk=stk, git=git)
        self.inputs: GithubInputs = GithubInputs(**kwargs)
        self.api = GithubApiClient(http_client=http_client, pat=self.inputs.pat)
        self.callback_url = "https://workflow-api.v1.stackspot.com/workflows/github/callback"

    @property
    def hook_exists(self) -> bool:
        logging.info("Checking if webhook is already configured...")
        response = self.api.get_repository_hooks(org_name=self.inputs.org_name, repo_name=self.inputs.repo_name)
        if response.ok:
            webhooks_list_response = response.json()
            workflow_hook = [
                hook
                for hook in webhooks_list_response
                if "config" in hook and hook["config"]["url"] == self.callback_url
            ]

            return bool(workflow_hook)
        logging.info("Failure listing github weebhooks")
        response.raise_for_status()

    def execute_repo_creation(self):
        self.api.create_repository(org_name=self.inputs.org_name, repo_name=self.inputs.repo_name)

    def repo_exists(self) -> bool:
        response = self.api.get_repository(org_name=self.inputs.org_name, repo_name=self.inputs.repo_name, raise_for_status=False)
        if response.ok:
            return True
        elif response.status_code == 404:
            return False
        logging.info("Failure getting github repository!")
        response.raise_for_status()

    @property
    def clone_url(self) -> str:
        return self.clone_url_mask.format(
            pat=self.inputs.pat,
            org_name=self.inputs.org_name,
            repo_name=self.inputs.repo_name
        )

    def create_pull_request(self) -> str:
        response = self.api.create_pull_request(
            org_name=self.inputs.org_name,
            repo_name=self.inputs.repo_name,
            pr_title=self.inputs.pr_title,
            head=self.inputs.ref_branch,
            base="main"
        )
        return response.json()['url']

    def extra_setup(self):
        if not self.hook_exists:
            logging.info("Webhook not found.")
            logging.info("Setting up repository webhook...")
            response = self.api.create_repository_hook(
                org_name=self.inputs.org_name,
                repo_name=self.inputs.repo_name,
                callback_url=self.callback_url
            )
            if response.ok:
                return
            logging.info("Failure creating repository callback webhook")
            response.raise_for_status()
        else:
            logging.info("Webhook is already configured.")

    @property
    def scm_config_url(self) -> str:
        return f"https://github.com/{self.inputs.org_name}/{self.inputs.repo_name}"
