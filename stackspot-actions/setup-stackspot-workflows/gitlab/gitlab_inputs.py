from provider import Inputs
from dataclasses import dataclass


@dataclass(frozen=True)
class GitlabInputs(Inputs):
    pat: str
    group_name: str
    project_name: str
