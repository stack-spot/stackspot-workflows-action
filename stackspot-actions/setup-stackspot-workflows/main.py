import logging
import time
from typing import Protocol

import requests

from azure.azure_provider import AzureProvider
from helpers.exceptions import ActionException
from helpers.git_helper import Git
from github.github_provider import GithubProvider
from gitlab.gitlab_provider import GitlabProvider
from bitbucket.bitbucket_provider import BitbucketProvider
from helpers.http_client import HttpClient
from provider import Provider
from setup import setup
from helpers.stk import Stk

logging.basicConfig(format="%(message)s", level=logging.INFO)

PROVIDERS = dict(Azure=AzureProvider, Github=GithubProvider, Gitlab=GitlabProvider, Bitbucket=BitbucketProvider)


class Metadata(Protocol):
    component_path: str
    target_path: str
    inputs: dict


def extra_inputs(metadata: Metadata):
    return dict(
        component_path=metadata.component_path,
        target_path=metadata.target_path,
        ref_branch=f"setup-scm-{str(time.time())}"
    )


def run(metadata: Metadata):
    logging.info("Start!")
    try:
        kwargs = dict(
            stk=Stk(),
            git=Git(),
            http_client=HttpClient(),
            **metadata.inputs,
            **extra_inputs(metadata)
        )
        provider_name = metadata.inputs.get("provider")
        provider: Provider = PROVIDERS[provider_name](**kwargs)
        setup(provider)
    except requests.HTTPError:
        logging.error("A failure with a important request happened")
    except ActionException as e:
        logging.error(e.msg)
    except Exception as e:
        logging.exception(e)
    logging.info("Exit!")
