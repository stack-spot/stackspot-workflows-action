import logging
import requests

GET_REPOSITORY_SERVICE_URL = "https://{domain}/repos/{org_name}/{repo_name}"
CREATE_REPOSITORY_SERVICE_URL = "https://{domain}/orgs/{org_name}/repos"
CREATE_PULL_REQUEST_SERVICE_URL = "https://{domain}/repos/{org_name}/{repo_name}/pulls"
GET_REPOSITORY_HOOKS_SERVICE_URL = "https://{domain}/repos/{org_name}/{repo_name}/hooks"
CREATE_REPOSITORY_HOOKS_SERVICE_URL = "https://{domain}/repos/{org_name}/{repo_name}/hooks"


class GithubApiClient:
    def __init__(self, **kwargs):
        self.http_client = kwargs.get("http_client")
        self.pat = kwargs.get("pat")
        self.domain = "api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.pat}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_repository(self, org_name: str, repo_name: str, raise_for_status: bool = True) -> requests.Response:
        return self.http_client.get(
            url=GET_REPOSITORY_SERVICE_URL.format(domain=self.domain, org_name=org_name, repo_name=repo_name),
            headers=self.headers,
            title="github get repository",
            raise_for_status=raise_for_status,
        )

    def create_repository(self, org_name: str, repo_name: str) -> requests.Response:
        logging.info("Github create repository...")
        return self.http_client.post(
            url=CREATE_REPOSITORY_SERVICE_URL.format(domain=self.domain, org_name=org_name, repo_name=repo_name),
            headers=self.headers,
            json={
                "name": repo_name,
                "description": "StackSpot Workflows",
                "homepage": "https://stackspot.com",
                "private": True,
            },
            title="github create repository",
            raise_for_status=True,
        )

    def get_repository_hooks(self, org_name: str, repo_name: str) -> requests.Response:
        logging.info("Github get repository hooks...")
        return self.http_client.get(
            url=GET_REPOSITORY_HOOKS_SERVICE_URL.format(domain=self.domain, org_name=org_name, repo_name=repo_name),
            headers=self.headers,
            title="github get repository hooks",
            raise_for_status=True,
        )

    def create_repository_hook(self, org_name: str, repo_name: str, callback_url: str) -> requests.Response:
        logging.info("Github create repository hooks...")
        return self.http_client.post(
            url=CREATE_REPOSITORY_HOOKS_SERVICE_URL.format(domain=self.domain, org_name=org_name, repo_name=repo_name),
            headers=self.headers,
            json={
                "name": "web",
                "active": True,
                "events": ["workflow_job", "workflow_run"],
                "config": {
                    "url": callback_url,
                    "content_type": "json",
                    "insecure_ssl": "0",
                },
            },
            title="github create repository hook",
            raise_for_status=True,
        )

    def create_pull_request(self, org_name: str, repo_name: str, pr_title: str, head: str, base: str) -> requests.Response:
        logging.info("Github create pull request...")
        return self.http_client.post(
            url=CREATE_PULL_REQUEST_SERVICE_URL.format(domain=self.domain, org_name=org_name, repo_name=repo_name),
            headers=self.headers,
            json={"title": pr_title, "head": head, "base": base},
            title="github create pull request",
            raise_for_status=True,
        )
