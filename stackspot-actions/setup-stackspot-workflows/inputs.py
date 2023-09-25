from dataclasses import dataclass


@dataclass(frozen=True)
class Inputs:
    repo_name: str
    create_repo: str
    provider: str
    ref_branch: str
    target_path: str
    component_path: str

    @property
    def pr_title(self) -> str:
        return "Stackspot Update workflow configuration."
