from inputs import Inputs
from dataclasses import dataclass


@dataclass(frozen=True)
class AzureInputs(Inputs):
    pat: str
    org_name: str
    project_name: str
