# Usage

If you wanna execute it locally, you will need stackspot cli installed, then execute:

```
stk run action <path> --inputs-json '{
    "visibility": "[private|public]", 
    "group_name": "<group_name>", 
    "token": "<gitlab_token>", 
    "name": "<repository_name>"
}'
```