import logging
from .provider import Provider, Inputs

class UrlBuilder:
    def __init__(self, inputs: Inputs):
        self.inputs = inputs
        self.base_url = f"https://dev.azure.com/{inputs.org_name}"
        self.paths = []
    
    def path(self, path: str) -> "UrlBuilder":
        self.paths.append(path)
        return self
    
    def build(self) -> str:
        return "/".join([self.base_url, *self.paths])

class GithubProvider(Provider):

    def execute_repo_creation(self, inputs: Inputs):
        raise Exception("Not Implemented yet!")
        
    def repo_exists(self, inputs: Inputs) -> bool:
        raise Exception("Not Implemented yet!")
    
    def clone_url(self, inputs: Inputs) -> str:
        raise Exception("Not Implemented yet!")

    def execute_provider_setup(self, inputs: Inputs):
        raise Exception("Not Implemented yet!")