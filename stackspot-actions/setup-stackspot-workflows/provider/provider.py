import logging
import tempfile
import time
import os
import sys
import shutil
import stat
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .errors import RepoAlreadyExistsError, RepoDoesNotExistError, CloningRepoError, GitUserSetupError


# This handler is necessary to make remove_stack_dir in Windows
# @see https://stackoverflow.com/questions/2656322/shutil-rmtree-fails-on-windows-with-access-is-denied
def on_delete_error(func, path, exc_info):
    # Is the error an access error?
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


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
    use_self_hosted_pool: Optional[bool] = None
    self_hosted_pool_name: Optional[str] = None
    project_name: Optional[str] = None
    client_key: Optional[str] = None
    client_secret: Optional[str] = None


class Provider(ABC):
    def setup(self, inputs: Inputs):
        self.check_git_configuration()
        logging.info("Setting up %s SCM...", inputs.provider)
        cwd = os.getcwd()
        self.execute_pre_setup_provider(inputs)
        if inputs.create_repo:
            self.create_repo(inputs)
            time.sleep(5)
        elif not self.repo_exists(inputs):
            raise RepoDoesNotExistError()
        workdir = tempfile.mkdtemp()
        try:
            self.clone_created_repo(workdir, inputs)
            self.create_workflow_files(workdir, inputs)
            self.commit_and_push()
        finally:
            os.chdir(cwd)
            shutil.rmtree(workdir, onerror=on_delete_error, ignore_errors=True)
        self.execute_provider_setup(inputs)

    def check_git_configuration(self):
        result_user_name = os.system("git config --global user.name")
        result_user_email = os.system("git config --global user.email")
        if (result_user_name + result_user_email) > 0:
            raise GitUserSetupError()

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
        stk = sys.argv[0]
        self._remove_all_files_generated_on_apply_plugin(inputs)
        stk_apply_plugin_cmd = (
            f"{stk} apply plugin {inputs.component_path} --skip-warning "
            f"--provider {inputs.provider} "
        )
        if inputs.use_self_hosted_pool is not None:
            stk_apply_plugin_cmd += f"--use_self_hosted_pool {inputs.use_self_hosted_pool} "
        if inputs.self_hosted_pool_name is not None:
            stk_apply_plugin_cmd += f"--self_hosted_pool_name {inputs.self_hosted_pool_name} "
        os.system(stk_apply_plugin_cmd)
        shutil.rmtree(".stk", onerror=on_delete_error)

    def commit_and_push(self):
        logging.info("Commiting and pushing workflow files to repo...")
        os.system('git branch -m main && git add . && git commit -m "Initial commit" && git push origin main')

    def _remove_all_files_generated_on_apply_plugin(self, inputs: Inputs):
        workflow_template_provider_path = Path(inputs.component_path) / "workflow-templates" / inputs.provider.lower()
        workdir = os.getcwd()

        for subdir, dirs, files in os.walk(workflow_template_provider_path):
            for file in files:
                file_to_be_applied_path = Path(os.path.join(subdir, file))
                relative_path_file_to_be_applied = file_to_be_applied_path.relative_to(workflow_template_provider_path)

                file_path = Path(workdir) / inputs.repo_name / relative_path_file_to_be_applied
                if file_path.exists():
                    file_path.unlink(missing_ok=True)

    @abstractmethod
    def execute_pre_setup_provider(self, inputs: Inputs):
        ...

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
