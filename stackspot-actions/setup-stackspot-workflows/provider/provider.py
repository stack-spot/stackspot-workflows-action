import logging
import subprocess
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

from questionary import confirm

from .errors import (
    RepoAlreadyExistsError,
    RepoDoesNotExistError,
    CloningRepoError,
    GitUserSetupError,
    WorkspaceShouldNotInUseError,
    ApplyPluginSetupRepositoryError,
)


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
    ref_branch: Optional[str] = None


class Provider(ABC):
    def __init__(self):
        self.stk = Optional[str]

    def setup(self, inputs: Inputs):
        self.stk = sys.argv[0]
        self.check_git_configuration()
        self._check_workspace_in_use()

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
            if not self.check_if_main_exists():
                self.create_workflow_files(inputs)
                self.commit_and_push("main")
            else:
                self.create_new_branch_from_base(inputs.ref_branch, "main")
                self.create_workflow_files(inputs)
                if self.is_workflow_changed():
                    self.commit_and_push(inputs.ref_branch, True)
                    self.create_pull_request(inputs)
                else:
                    logging.info("Workflow files are up to date.")
        except Exception as e:
            logging.exception(e)
            raise e
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
        try:
            logging.info("Creating workflow files...")
            self._remove_all_files_generated_on_apply_plugin(inputs)
            stk_apply_plugin_cmd = [
                self.stk,
                "apply",
                "plugin",
                str(inputs.component_path),
                "--skip-warning",
                "--provider",
                inputs.provider,
            ]
            if inputs.use_self_hosted_pool is not None:
                stk_apply_plugin_cmd.extend(
                    ["--use_self_hosted_pool", str(inputs.use_self_hosted_pool)]
                )
            if inputs.self_hosted_pool_name is not None:
                stk_apply_plugin_cmd.extend(
                    ["--self_hosted_pool_name", inputs.self_hosted_pool_name]
                )
            result = subprocess.run(stk_apply_plugin_cmd)
            if result.returncode != 0:
                raise ApplyPluginSetupRepositoryError()
        finally:
            shutil.rmtree(".stk", onerror=on_delete_error, ignore_errors=True)

    def check_if_main_exists(self) -> bool:
        logging.info("Checking if the main branch exists...")
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", "main"],
            capture_output=True,
            text=True,
        )
        return bool(result.stdout)

    def is_workflow_changed(self):
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
        )
        return bool(result.stdout)

    def create_new_branch_from_base(self, branch: str, base_branch: str):
        logging.info(f"Creting new branch {branch}...")
        os.system(f"git checkout {base_branch} && git pull && git checkout -b {branch}")

    def commit_and_push(self, branch: str, existing: bool = False):
        logging.info(f"Commiting and pushing workflow files to branch {branch}")

        if existing:
            os.system(
                f'git add . && git commit -m "Update commit" && git push origin {branch}'
            )
        else:
            os.system(
                f'git branch -m {branch} && git add . && git commit -m "Initial commit" && git push origin {branch}'
            )

    def _remove_all_files_generated_on_apply_plugin(self, inputs: Inputs):
        workflow_template_provider_path = (
            Path(inputs.component_path) / "workflow-templates" / inputs.provider.lower()
        )
        workdir = os.getcwd()

        for subdir, dirs, files in os.walk(workflow_template_provider_path):
            for file in files:
                file_to_be_applied_path = Path(os.path.join(subdir, file))
                relative_path_file_to_be_applied = file_to_be_applied_path.relative_to(
                    workflow_template_provider_path
                )

                file_path = Path(workdir) / relative_path_file_to_be_applied
                if file_path.exists():
                    file_path.unlink(missing_ok=True)

    def _check_workspace_in_use(self):
        logging.info("Validating workspace is use...")
        home_path = Path.home()
        stk_binary_name = Path(self.stk).stem
        stk_folder = Path(home_path) / f".{stk_binary_name}"
        workspace_config_path = stk_folder / "workspaces" / "workspace-config.json"

        if workspace_config_path.exists():
            should_exit_workspace = confirm(
                message="You need to be outside workspace, do you agree to exit current workspace?"
            ).unsafe_ask()
            if not should_exit_workspace:
                raise WorkspaceShouldNotInUseError()
            exit_workspace_cmd = [self.stk, "exit", "workspace"]
            subprocess.run(exit_workspace_cmd)

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

    @abstractmethod
    def create_pull_request(self, inputs: Inputs) -> str:
        ...
