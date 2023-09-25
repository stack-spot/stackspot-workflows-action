import logging
import time
from typing import Protocol
from azure.azure_provider import AzureProvider
from github.github_provider import GithubProvider
from gitlab.gitlab_provider import GitlabProvider
from http_client import HttpClient
from setup import setup

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

PROVIDERS = dict(Azure=AzureProvider, Github=GithubProvider, Gitlab=GitlabProvider)


class Metadata(Protocol):
    component_path: str
    target_path: str
    inputs: dict


def extra_inputs(metadata: Metadata):
    return dict(
        component_path=metadata.component_path,
        target_path=metadata.target_path,
        ref_branch=f"stackspot/setup-scm-{str(time.time())}"
    )


def run(metadata: Metadata):
    logging.info("Starting!")
    try:
        setup(
            PROVIDERS[metadata.inputs.get("provider")](
                http_client=HttpClient(), **metadata.inputs, **extra_inputs(metadata)
            )
        )
    except Exception as e:
        logging.exception(e)
    logging.info("Exit!")
