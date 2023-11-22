import json
import logging
from github import GithubCreateRepository

logger = logging.getLogger()
myFormatter = logging.Formatter('[GITHUB CREATE REPO ACTION] >> %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(myFormatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def export_repository_url(repository_url: str):
    logger.info("Writing repository url into stk cli context file to be used by pipeline ...")
    with open("stk-local-context.json", "w") as file:
        json.dump(dict(outputs=dict(created_repository=repository_url)), file, indent=4)


def run(metadata):
    inputs = metadata.inputs
    repository_name = inputs.get("repository_name")
    repository_description = inputs.get("description")
    visibility = inputs.get("visibility")

    create_repo = GithubCreateRepository(**inputs)
    repository_url = create_repo(
        repository_name=repository_name,
        repository_description=repository_description,
        visibility=visibility
    )

    export_repository_url(repository_url=repository_url)
