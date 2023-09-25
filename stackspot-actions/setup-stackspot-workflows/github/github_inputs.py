from provider import Inputs
from dataclasses import dataclass


@dataclass(frozen=True)
class GithubInputs(Inputs):
    pat: str
    org_name: str
    repo_name: str
