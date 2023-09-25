import logging
import subprocess
import os

from errors import (
    CloningRepoError,
    GitUserSetupError,
)

from provider import Provider


def clone(workdir: str, provider: Provider):
    logging.info("Cloning created repository...")
    clone_url = provider.clone_url()
    os.chdir(workdir)
    if os.system(f"git clone {clone_url}") != 0:
        raise CloningRepoError()
    os.chdir(provider.inputs.repo_name)


def commit_and_push(branch: str, existing: bool = False):
    logging.info(f"Commiting and pushing workflow files to branch {branch}")
    if existing:
        os.system(f'git add . && git commit -m "Update commit" && git push origin {branch}')
    else:
        os.system(f'git branch -m {branch} && git add . && git commit -m "Initial commit" && git push origin {branch}')


def create_new_branch(branch: str, base_branch: str):
    logging.info(f"Creting new branch {branch}...")
    os.system(f"git checkout {base_branch} && git pull && git checkout -b {branch}")


def check_configuration():
    if os.system("git config --global user.name") or os.system("git config --global user.email"):
        raise GitUserSetupError()


def check_if_main_exists() -> bool:
    logging.info("Checking if the main branch exists...")
    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", "main"],
        capture_output=True,
        text=True,
    )
    return bool(result.stdout)


def is_status_changed():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    return bool(result.stdout)
