from ..bibucket_inputs import Bi


class UrlBuilder:
    def __init__(self, inputs: Inputs):
        self.inputs = inputs
        self.base_url = "https://api.bitbucket.org/2.0"
        self.paths = []

    def path(self, path: str) -> "UrlBuilder":
        self.paths.append(path)
        return self

    def build(self) -> str:
        return "/".join([self.base_url, *self.paths])


class PipelineVariable:
    def __init__(self, key: str, value: str, secured=False):
        self.key = key
        self.value = value
        self.secured = secured
