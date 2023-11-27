## Gitlab create repository action

Action created by Stackspot to be used into workspace workflows as a before action to create a repository, when the account scm provider is Gitlab.
The action is functional, but it was build to be simple as an example of how actions of create repository should be implemented.

Feel free to clone it and add features before publish it into your studio. But first, before modifying,
there are two points of implementation that a developer should pay attention:

1. Stackspot workflow api by default, when identifies a "create repository action", 
it adds 5 hidden inputs to the stk run action workflow call. 
Even if you do not declare then in action.yml they will be added. 
But if you declare then in action manifest, the stackspot portal will ask these inputs when you try to dispatch a workflow, then they will not be overwritten. 
These inputs are:
    - name: copied from the app/infra which will be created by the workflow.
    - description: copied from the description of the app/infra which will be created by the workflow.
    - org: its the group_name from the workflow url, which is configured into scm integration page.
    - token: The token which was configured into scm integration page, it is used to create the repository by the gitlab api.
    - workflow_api_authorization: A valid token with the same rules of portal user, which dispatched the workflow, that token can be used to call stackspot apis.

2. For now, to the workflow work well, the action need to open a file named "stk-local-context.json" and write the name of created repository as value of the following key in the object:
```json
{
    "outputs": {
        "created_repository": "<https_repository_clone_path>"
    }
}
```