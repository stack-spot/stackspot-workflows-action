import logging
import tempfile
import time
import os
import shutil
import git_helper as git
import stk
from errors import RepoAlreadyExistsError, RepoDoesNotExistError

from provider import Provider


def create_repo(provider: Provider):
    if provider.inputs.create_repo:
        logging.info("Creating repository to host StackSpot workflows...")
        if provider.repo_exists():
            raise RepoAlreadyExistsError()
        provider.execute_repo_creation()
        time.sleep(5)
    elif not provider.repo_exists():
        raise RepoDoesNotExistError()


def setup(provider: Provider):
    pr_link = None
    git.check_configuration()
    stk.check_workspace_in_use()

    logging.info("Setting up %s SCM...", provider.inputs.provider)
    cwd = os.getcwd()
    provider.execute_pre_setup_provider()

    create_repo(provider)

    workdir = tempfile.mkdtemp()
    try:
        git.clone(workdir, provider)
        if not git.check_if_main_exists():
            stk.create_workflow_files(provider)
            git.commit_and_push("main")
        else:
            git.create_new_branch(provider.inputs.ref_branch, "main")
            stk.create_workflow_files(provider)
            if git.is_status_changed():
                git.commit_and_push(provider.inputs.ref_branch, True)
                pr_link = provider.create_pull_request()
            else:
                logging.info("Workflow files are up to date.")
    except Exception as e:
        logging.exception(e)
        raise e
    finally:
        os.chdir(cwd)
        shutil.rmtree(workdir, onerror=stk.on_delete_error, ignore_errors=True)
    provider.execute_provider_setup()

    logging.info("...")
    logging.info("Setup concluded successfully!")
    logging.info(f"Use this url: {provider.scm_config_url} into scm configuration page of Stackspot")
    if pr_link:
        logging.info(f"But first review and accept this pull request: {pr_link}")
    logging.info("...")
