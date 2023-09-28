import os
import shutil
import logging
from helpers import util
from provider import Provider


def setup(provider: Provider):
    provider.validate_environment()
    cwd = os.getcwd()
    provider.create_repository()
    try:
        provider.clone_repository()
        provider.create_workflow_manifest()
        pr_link = provider.save_files_repository()
        provider.extra_setup()
    finally:
        os.chdir(cwd)
        shutil.rmtree(provider.workdir, onerror=util.on_delete_error, ignore_errors=True)

    logging.info("...")
    logging.info("Setup concluded successfully!")
    logging.info(f"Use this url: {provider.scm_config_url} into scm configuration page of Stackspot")
    pr_link and logging.info(f"Review and accept this pr: {pr_link} to use workflows!")
    logging.info("...")
