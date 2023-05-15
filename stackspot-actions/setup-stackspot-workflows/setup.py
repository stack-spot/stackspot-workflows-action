import logging
from dataclasses import fields
from typing import Protocol, Mapping
from provider import Inputs, Provider
from provider.errors import RepoAlreadyExistsError, UnauthorizedError, RepoDoesNotExistError
from provider.github import GithubProvider
from provider.azure import AzureProvider

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

class Metadata(Protocol):
    component_path: str
    target_path: str
    inputs: dict

PROVIDERS: Mapping[str, Provider] = {
    "Azure": AzureProvider(),
    "Github": GithubProvider(),
}

def parse_inputs(metadata: Metadata) -> Inputs:
    inputs = metadata.inputs
    field_values = { field.name: inputs.get(field.name) for field in fields(Inputs) }
    kwargs = {
        **field_values,
        "component_path": metadata.component_path,
        "target_path": metadata.target_path,
    }
    return Inputs(**kwargs)

def run(metadata: Metadata):
    print()
    try:
        inputs = parse_inputs(metadata)
        provider = PROVIDERS[inputs.provider]
        provider.setup(inputs)
    except UnauthorizedError:
        logging.error("Unauthorized!")
    except RepoAlreadyExistsError:
        logging.error("Repository already exists!")
    except RepoDoesNotExistError:
        logging.error("Repository provided doesn't exist and creation was not requested!")
    except:
        logging.exception("Unhandled error happened!")
    print()