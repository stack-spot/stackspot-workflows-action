from abc import ABC, abstractmethod
from inputs import Inputs


class Provider(ABC):
    inputs: Inputs

    @abstractmethod
    def execute_pre_setup_provider(self):
        ...

    @abstractmethod
    def execute_provider_setup(self):
        ...

    @abstractmethod
    def execute_repo_creation(self):
        ...

    @abstractmethod
    def repo_exists(self) -> bool:
        ...

    @abstractmethod
    def clone_url(self) -> str:
        ...

    @abstractmethod
    def create_pull_request(self) -> str:
        ...

    @property
    @abstractmethod
    def scm_config_url(self) -> str:
        ...
