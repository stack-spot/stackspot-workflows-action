# Usage

To execute it locally, it's needed [stackspot cli](https://docs.stackspot.com/home/stk-cli/install) installed, then execute:

```
stk run action <path> --inputs-json '{
    "visibility": "[PRIVATE|PUBLIC]", 
    "project_name": "<project_name>", 
    "token": "<bitbucket_token>", 
    "name": "<repository_name>",
    "org": "<workspace_name>"
}'
```

To execute it with Stackspot workflow, just follow the steps: 
1. [Publish the action](https://docs.stackspot.com/guides/studio-guides/publish-action/)
2. [Add it to a stack](https://docs.stackspot.com/guides/studio-guides/create-stack/)
3. [Add the stack to a workspace](https://docs.stackspot.com/home/workspace/add-stacks/)
4. [Configure the workspace workflow](https://docs.stackspot.com/home/workspace/configure-workflow/)
