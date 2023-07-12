import logging
from dataclasses import fields
import time
from typing import Protocol, Mapping

import questionary
from templateframework.prompt.validation import NotEmpty

from provider.bitbucket import BitBucketProvider
from provider import Inputs, Provider
from provider.errors import RepoAlreadyExistsError, UnauthorizedError, RepoDoesNotExistError, GitUserSetupError, \
    WorkspaceShouldNotInUseError, ApplyPluginSetupRepositoryError
from provider.github import GithubProvider
from provider.azure import AzureProvider

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

GIT_USER_SETUP_ERROR_MESSAGE = """You must setup your git user before run this action!
Use the following commands to setup your git user:
git config --global user.name \"Your Name\"
git config --global user.email your-email@your-company.com"""

PROVIDER_BITBUCKET_LOWERED = "bitbucket"


class Metadata(Protocol):
    component_path: str
    target_path: str
    inputs: dict


PROVIDERS: Mapping[str, Provider] = {
    "Azure": AzureProvider(),
    "BitBucket": BitBucketProvider(),
    "Github": GithubProvider(),
}


class NotEmptyStripped(NotEmpty):
    def valid(self, value: str) -> bool:
        return super().valid(value.strip())


def __ask_self_hosted_pool_names(inputs):
    provider = inputs.get("provider", "").lower()
    use_self_hosted_pool = inputs.get("use_self_hosted_pool", False)
    self_hosted_pool_name = __get_self_hosted_pool_name(inputs)

    if provider == PROVIDER_BITBUCKET_LOWERED:
        if __should_ask_self_hosted_pool_name(use_self_hosted_pool, self_hosted_pool_name):
            inputs["self_hosted_pool_name"] = questionary.text(
                message="Inform your runners separated by comma (E.g.: 'self.hosted,linux'):",
                default="self.hosted,linux",
                validate=NotEmptyStripped).unsafe_ask()
    else:
        if __should_ask_self_hosted_pool_name(use_self_hosted_pool, self_hosted_pool_name):
            inputs["self_hosted_pool_name"] = questionary.text(
                message="Which self-hosted runner group do you want to use?",
                validate=NotEmptyStripped).unsafe_ask()

    return inputs


def __get_self_hosted_pool_name(inputs):
    self_hosted_pool_name = inputs.get("self_hosted_pool_name", "")
    if self_hosted_pool_name:
        return self_hosted_pool_name

    return inputs.get("self-hosted-pool-name", "")


def __should_ask_self_hosted_pool_name(use_self_hosted_pool: bool, self_hosted_pool_name: str):
    return use_self_hosted_pool and not self_hosted_pool_name


def __parse_inputs(metadata: Metadata) -> Inputs:
    inputs = metadata.inputs
    inputs = __ask_self_hosted_pool_names(inputs)
    field_values = {field.name: inputs.get(field.name) for field in fields(Inputs)}
    timestamp = int(time.time())
    kwargs = {
        **field_values,
        "component_path": metadata.component_path,
        "target_path": metadata.target_path,
        "ref_branch": f"stackspot/setup-scm-{timestamp}"
    }
    return Inputs(**kwargs)


def run(metadata: Metadata):
    print()
    try:
        inputs = __parse_inputs(metadata)
        provider = PROVIDERS[inputs.provider]
        provider.setup(inputs)
    except UnauthorizedError:
        logging.error("Unauthorized!")
    except RepoAlreadyExistsError:
        logging.error("Repository already exists!")
    except RepoDoesNotExistError:
        logging.error("Repository provided doesn't exist and creation was not requested!")
    except WorkspaceShouldNotInUseError:
        logging.error("Workspace should not be in use!")
    except ApplyPluginSetupRepositoryError:
        # Exception handling is ignored due to
        # apply plugin command has already generated an output message
        pass
    except GitUserSetupError:
        logging.error(GIT_USER_SETUP_ERROR_MESSAGE)
    except:
        logging.exception("Unhandled error happened!")
    print()
