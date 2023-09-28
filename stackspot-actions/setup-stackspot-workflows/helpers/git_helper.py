import logging
import subprocess
import os

from helpers.exceptions import CloningRepoException


class Git:
    @property
    def has_user_name(self):
        return bool(os.system("git config --global user.name"))

    @property
    def has_user_email(self):
        return bool(os.system("git config --global user.email"))

    @staticmethod
    def clone(clone_url: str, workdir: str):
        cmd = f"git clone {clone_url} {workdir}"
        if os.system(cmd) != 0:
            raise CloningRepoException()
        os.chdir(workdir)

    @staticmethod
    def commit(msg: str):
        cmd = f"git commit -m '{msg}'"
        logging.info(cmd)
        os.system(cmd)

    @staticmethod
    def push(branch: str):
        cmd = f"git push -u origin {branch}"
        logging.info(cmd)
        os.system(cmd)

    @staticmethod
    def add():
        cmd = f"git add ."
        logging.info(cmd)
        os.system(cmd)

    @staticmethod
    def main_exists() -> bool:
        logging.info("Checking if the main branch exists...")
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", "main"],
            capture_output=True,
            text=True,
        )
        return bool(result.stdout)

    @staticmethod
    def checkout(branch: str):
        cmd = f"git checkout -b {branch}"
        logging.info(cmd)
        os.system(cmd)

    @staticmethod
    def is_status_changed():
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
        )
        return bool(result.stdout)
