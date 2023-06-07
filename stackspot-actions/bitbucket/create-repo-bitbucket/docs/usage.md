This action can be used to create a bitbucket repository.

The workspace must exists before running this action, it's no possible to create an workspace using the REST API.

Example:

stk run action stackspot-actions/create-repo-bitbucket --token **** --workspace_name <workspace-name> --project_name <project-name> --repo_name <repo-name>