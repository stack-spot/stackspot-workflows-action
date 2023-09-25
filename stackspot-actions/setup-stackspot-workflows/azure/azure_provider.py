import logging

from http_client import HttpClient
from provider import Provider
from azure.azure_inputs import AzureInputs
from azure.azure_api_client import AzureApiClient


class AzureProvider(Provider):
    PIPELINE_NAME = "middle-flow"
    clone_url_mask = "https://{org_name}:{pat}@dev.azure.com/{org_name}/{project_name}/_git/{repository_name}"

    def __init__(self, http_client: HttpClient, **kwargs):
        super().__init__()
        self.inputs: AzureInputs = AzureInputs(repo_name=kwargs.get("project_name"), **kwargs)
        self.api = AzureApiClient(http_client=http_client, pat=self.inputs.pat)

    @property
    def repository_id(self):
        response = self.api.get_repository(
            org_name=self.inputs.org_name,
            project_name=self.inputs.project_name,
            repository_name=self.inputs.project_name,
        )
        if response.ok:
            return response.json()["id"]
        logging.info("Failure getting repository id to refer pipeline yaml")
        response.raise_for_status()

    @property
    def project_id(self) -> str:
        response = self.api.get_project(org_name=self.inputs.org_name, project_name=self.inputs.project_name)
        if response.ok:
            return response.json()["id"]
        logging.info(f"Failure getting project id: {self.inputs.org_name}/{self.inputs.project_name}")
        response.raise_for_status()

    def create_pull_request(self):
        response = self.api.create_pull_request(
            repository_id=self.repository_id,
            pr_title=self.inputs.pr_title,
            pr_description=self.inputs.pr_title,
            pr_source=self.inputs.ref_branch,
            pr_target="main"
        )
        if response.ok:
            return
        logging.info(f"Failure creating pr from: {self.inputs.ref_branch} to: main")
        response.raise_for_status()

    def execute_repo_creation(self):
        response = self.api.create_project(
            org_name=self.inputs.org_name,
            project_name=self.inputs.project_name,
        )
        if response.ok:
            return
        logging.info(f"Failure creating {self.inputs.project_name} into {self.inputs.org_name} organization!")
        response.raise_for_status()

    def repo_exists(self) -> bool:
        response = self.api.get_project(org_name=self.inputs.org_name, project_name=self.inputs.project_name)
        if response.ok:
            return True
        elif response.status_code == 404:
            return False
        logging.info(f"Failure getting azure project: {self.inputs.org_name}/{self.inputs.project_name}")
        response.raise_for_status()

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
            pipeline_name=self.PIPELINE_NAME
        )
        if response.ok:
            return
        elif response.status_code == 409:
            logging.info(f"Pipeline {self.PIPELINE_NAME} already exists")
            return
        response.raise_for_status()

    def _setup_github_connection(self):
        response = self.api.create_service_endpoint(
            org_name=self.inputs.org_name,
            project_name=self.inputs.project_name,
            github_pat=self.inputs.github_pat,
            project_id=self.project_id
        )
        if response.status_code == 500 and "DuplicateServiceConnectionException" in response.json().get("typeName"):
            logging.info("Git connection already exists with name stackspot_github_connection")
            return
        if not response.ok:
            logging.info("Failure creating service endpoint to git connection")
            response.raise_for_status()
        endpoint_id = response.json()["id"]

        response = self.api.update_pipeline_permission_endpoint(
            org_name=self.inputs.org_name,
            project_name=self.inputs.project_name,
            endpoint_id=endpoint_id
        )
        if response.ok:
            return
        logging.info("Failure giving permission to pipeline with the new service endpoint connection")
        response.raise_for_status()

    def execute_provider_setup(self):
        self._create_pipeline()
        self._setup_github_connection()

    @property
    def scm_config_url(self) -> str:
        return f"https://dev.azure.com/{self.inputs.org_name}/{self.inputs.project_name}"

    def execute_pre_setup_provider(self):
        pass
