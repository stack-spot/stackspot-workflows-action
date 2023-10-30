import logging
import tempfile
import time
from abc import ABC, abstractmethod
from typing import Optional

from questionary import confirm

from helpers.exceptions import RepositoryNeedsToExists
from helpers.git_helper import Git
from inputs import Inputs
from helpers.stk import Stk


class Provider(ABC):
    inputs: Inputs

    def __init__(self, stk: Stk, git: Git):
        self.stk = stk
        self.git = git
        self.workdir = tempfile.mkdtemp()
        self.repo_created = False

    @abstractmethod
    def extra_setup(self):
        ...

    @abstractmethod
    def execute_repo_creation(self):
        ...

    @abstractmethod
    def repo_exists(self) -> bool:
        ...

    @property
    @abstractmethod
    def clone_url(self) -> str:
        ...

    @abstractmethod
    def create_pull_request(self) -> str:
        ...

    @property
    @abstractmethod
    def scm_config_url(self) -> str:
        ...

    def validate_environment(self) -> bool:
        if not self.git.has_user_name:
            return False

        if not self.git.has_user_email:
            return False

        if self.stk.is_using_workspace:
            should_exit_workspace = confirm(
                message="You need to be outside workspace, do you agree to exit current workspace?"
            ).unsafe_ask()
            if not should_exit_workspace:
                return False
            self.stk.exit_workspace()
        return True

    def create_repository(self):
        if self.repo_exists():
            return
        logging.info("Repository not found!")
        create_repo = confirm(message="You want to create a new repository?").unsafe_ask()
        if create_repo:
            self.execute_repo_creation()
            self.repo_created = True
            time.sleep(5)
            return
        raise RepositoryNeedsToExists()

    def clone_repository(self):
        self.git.clone(self.clone_url, self.workdir)

    def create_workflow_manifest(self):
        self.stk.create_workflow_files(
            component_path=self.inputs.component_path,
            provider=self.inputs.provider
        )

    def save_files_repository(self) -> Optional[str]:
        working_branch = "main"
        self.git.init()
        if self.git.main_exists():
            self.git.checkout(self.inputs.ref_branch)
            working_branch = self.inputs.ref_branch
        else:
            if self.repo_created:
                self.git.checkout("main")

        if self.git.is_status_changed():
            self.git.add()
            self.git.commit(self.inputs.pr_title)
            self.git.push(working_branch)

            if not working_branch == "main":
                return self.create_pull_request()
