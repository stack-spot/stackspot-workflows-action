import json
import logging
from azure import AzureCreateRepository

logger = logging.getLogger()
myFormatter = logging.Formatter('[AZURE CREATE REPO ACTION] >> %(message)s')
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
    project_name = inputs.get("project_name")
    repo_name = inputs.get("repository_name")

    create_repo = AzureCreateRepository(**inputs)
    repository_url = create_repo(project_name=project_name, repo_name=repo_name)

    export_repository_url(repository_url=repository_url)
