import logging
import subprocess
import tempfile
import time
import os
import sys
import shutil
import stat
from pathlib import Path

from errors import (
    RepoAlreadyExistsError,
    RepoDoesNotExistError,
    CloningRepoError,
    GitUserSetupError,
    WorkspaceShouldNotInUseError,
    ApplyPluginSetupRepositoryError,
)
from questionary import confirm

from provider import Provider

stk = sys.argv[0]


# This handler is necessary to make remove_stack_dir in Windows
# @see https://stackoverflow.com/questions/2656322/shutil-rmtree-fails-on-windows-with-access-is-denied
def on_delete_error(func, path, exc_info):
    # Is the error an access error?
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def check_git_configuration():
    if os.system("git config --global user.name") or os.system("git config --global user.email"):
        raise GitUserSetupError()


def check_workspace_in_use():
    logging.info("Validating workspace is use...")
    home_path = Path.home()
    stk_binary_name = Path(stk).stem
    stk_folder = Path(home_path) / f".{stk_binary_name}"
    workspace_config_path = stk_folder / "workspaces" / "workspace-config.json"

    if workspace_config_path.exists():
        should_exit_workspace = confirm(
            message="You need to be outside workspace, do you agree to exit current workspace?"
        ).unsafe_ask()
        if not should_exit_workspace:
            raise WorkspaceShouldNotInUseError()
        exit_workspace_cmd = [stk, "exit", "workspace"]
        subprocess.run(exit_workspace_cmd)


def create_repo(provider: Provider):
    if provider.inputs.create_repo:
        logging.info("Creating repository to host StackSpot workflows...")
        if provider.repo_exists():
            raise RepoAlreadyExistsError()
        provider.execute_repo_creation()
        time.sleep(5)
    elif not provider.repo_exists():
        raise RepoDoesNotExistError()


def clone_created_repo(workdir: str, provider: Provider):
    logging.info("Cloning created repository...")
    clone_url = provider.clone_url()
    os.chdir(workdir)
    if os.system(f"git clone {clone_url}") != 0:
        raise CloningRepoError()
    os.chdir(provider.inputs.repo_name)


def check_if_main_exists() -> bool:
    logging.info("Checking if the main branch exists...")
    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", "main"],
        capture_output=True,
        text=True,
    )
    return bool(result.stdout)


def create_workflow_files(provider: Provider):
    try:
        logging.info("Creating workflow files...")
        remove_all_files_generated_on_apply_plugin(provider)
        stk_apply_plugin_cmd = [
            stk,
            "apply",
            "plugin",
            str(provider.inputs.component_path),
            "--skip-warning",
            "--provider",
            provider.inputs.provider,
            "--alias",
            "setup-scm"
        ]
        result = subprocess.run(stk_apply_plugin_cmd)
        if result.returncode != 0:
            raise ApplyPluginSetupRepositoryError()
    finally:
        shutil.rmtree(".stk", onerror=on_delete_error, ignore_errors=True)


def remove_all_files_generated_on_apply_plugin(provider: Provider):
    workflow_template_provider_path = (
            Path(provider.inputs.component_path) / "workflow-templates" / provider.inputs.provider.lower()
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


def commit_and_push(branch: str, existing: bool = False):
    logging.info(f"Commiting and pushing workflow files to branch {branch}")
    if existing:
        os.system(f'git add . && git commit -m "Update commit" && git push origin {branch}')
    else:
        os.system(f'git branch -m {branch} && git add . && git commit -m "Initial commit" && git push origin {branch}')


def create_new_branch_from_base(branch: str, base_branch: str):
    logging.info(f"Creting new branch {branch}...")
    os.system(f"git checkout {base_branch} && git pull && git checkout -b {branch}")


def is_workflow_changed():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    return bool(result.stdout)


def setup(provider: Provider):
    pr_link = None
    check_git_configuration()
    check_workspace_in_use()

    logging.info("Setting up %s SCM...", provider.inputs.provider)
    cwd = os.getcwd()
    provider.execute_pre_setup_provider()

    create_repo(provider)

    workdir = tempfile.mkdtemp()
    try:
        clone_created_repo(workdir, provider)
        if not check_if_main_exists():
            create_workflow_files(provider)
            commit_and_push("main")
        else:
            create_new_branch_from_base(provider.inputs.ref_branch, "main")
            create_workflow_files(provider)
            if is_workflow_changed():
                commit_and_push(provider.inputs.ref_branch, True)
                pr_link = provider.create_pull_request()
            else:
                logging.info("Workflow files are up to date.")
    except Exception as e:
        logging.exception(e)
        raise e
    finally:
        os.chdir(cwd)
        shutil.rmtree(workdir, onerror=on_delete_error, ignore_errors=True)
    provider.execute_provider_setup()

    logging.info("...")
    logging.info("Setup concluded successfully!")
    logging.info(f"Use this url: {provider.scm_config_url} into scm configuration page of Stackspot")
    if pr_link:
        logging.info(f"But first review and accept this pull request: {pr_link}")
    logging.info("...")
