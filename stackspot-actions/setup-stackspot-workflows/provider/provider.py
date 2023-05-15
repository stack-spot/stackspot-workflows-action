import logging
import tempfile
import time
import os
from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .errors import RepoAlreadyExistsError, RepoDoesNotExistError, CloningRepoError

@dataclass(frozen=True)
class Inputs:
    component_path: str
    create_repo: bool
    org_name: str
    pat: str
    provider: str
    repo_name: str
    target_path: str
    github_pat: Optional[str] = None

class Provider(ABC):

    def setup(self, inputs: Inputs):
        logging.info("Setting up %s SCM...", inputs.provider)
        if inputs.create_repo:
            self.create_repo(inputs)
            time.sleep(5)
        elif not self.repo_exists(inputs):
            raise RepoDoesNotExistError()
        with tempfile.TemporaryDirectory() as workdir:
            self.clone_created_repo(workdir, inputs)
            self.create_workflow_files(inputs)
            self.commit_and_push()
        self.execute_provider_setup(inputs)

    def create_repo(self, inputs: Inputs):
        logging.info("Creating repository to host StackSpot workflows...")
        if self.repo_exists(inputs):
            raise RepoAlreadyExistsError()
        self.execute_repo_creation(inputs)

    def clone_created_repo(self, workdir: str, inputs: Inputs):
        logging.info("Cloning created repository...")
        clone_url = self.clone_url(inputs)
        os.chdir(workdir)
        result = os.system(f"git clone {clone_url}")
        if result != 0:
            raise CloningRepoError()
        os.chdir(inputs.repo_name)
    
    def create_workflow_files(self, inputs: Inputs):
        logging.info("Creating workflow files...")
        os.system(f"rm -f create-app.yml crate-infra.yml run-action.yml")
        stk_apply_plugin_cmd = (
            f"stk-alpha apply plugin {inputs.component_path} --skip-warning "
            f"--provider {inputs.provider} "
            f"--org_name {inputs.org_name} "
            f"--repo_name {inputs.repo_name} "
            f"--create_repo {inputs.create_repo}"
        )
        os.system(stk_apply_plugin_cmd)
        os.system(f"rm -rf .stk")

    def commit_and_push(self):
        logging.info("Commit and push workflow files to repo...")
        os.system(f"git branch -m main && git add . && git commit -m 'Initial commit' && git push origin main")

    @abstractmethod
    def execute_provider_setup(self, inputs: Inputs):
        ...

    @abstractmethod
    def execute_repo_creation(self, inputs: Inputs):
        ...

    @abstractmethod
    def repo_exists(self, inputs: Inputs) -> bool:
        ...

    @abstractmethod
    def clone_url(self, inputs: Inputs) -> str:
        ...