from provider import Inputs
from dataclasses import dataclass


@dataclass(frozen=True)
class BitbucketInputs(Inputs):
    client_key: str
    client_secret: str
    workspace_name: str
    project_name: str
    repo_name: str
