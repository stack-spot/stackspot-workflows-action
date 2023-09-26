# Usage

Here are some commands to execute and test this action locally.

Notice that all those commands are executed **inside the action's folder** and they use the variable `stk_access_token` containing the user's access token. So that, before executing these commands, you must define the variable as below:

```sh
export stk_access_token="my-access-token-pat"
```

Also notice that you must set the JSON attributes `org` (similar to group), `project_name` (similar to repository name) and ``visibility` (public or private) properly.

### 1. How to execute this action locally

Inside the action's folder, execute the commando below:

```sh
stk run action -i "{\"token\": \"$stk_access_token\", \"project_name\": \"demo-$(date +%s)\", \"group_name\": \"stackspot\", \"visibility\": \"private\"}" --non-interactive .
```

If the command executes correctly, you will see an output like this:

```
> Getting the Group ID by the informed group name 'StackSpot'.
> Checking if the project (repository) 'demo-1693864337' exists in the group 'StackSpot' (group_id=71401813).
> Project (repository) 'demo-1693864337' not found in the group 'StackSpot' (group_id=71401813).
> Creating project (repository) 'demo-1693864337' in the group 'StackSpot' (group_id=71401813).
> Project (repository) 'demo-1693864337' created in the group 'StackSpot' with visibility 'private'.
```

### 2. Executing with disabled HTTP SSL Verify (`GITLAB_HTTP_SSL_VERIFY_ENABLED=false`)

By default, the SSL verify is enabled. But if you have any SSL issue, like expired root certificate or something like that, you may disable the SSL verify in Python's Requests libary. For that, just set the `dev__enable_ssl_verify` property to `false`:

```sh
export GITLAB_HTTP_SSL_VERIFY_ENABLED=false
stk run action -i "{\"token\": \"$stk_access_token\", \"project_name\": \"demo-$(date +%s)\", \"group_name\": \"stackspot\", \"visibility\": \"private\"}" --non-interactive .
```

You should disable this check for testing purposes only.

### 3. Executing with enabled HTTP logging (`GITLAB_HTTP_LOGGING_ENABLED=true`)

By default, the HTTP logging is **disabled** due to its verbosity. However, enabling it can be helpful when doing troubleshooting. For that, just set the `dev__enable_logging` property to `true`:

```sh
export GITLAB_HTTP_LOGGING_ENABLED=true
stk run action -i "{\"token\": \"$stk_access_token\", \"project_name\": \"demo-$(date +%s)\", \"group_name\": \"stackspot\", \"visibility\": \"private\"}" --non-interactive .
```

You should enable the logging for testing purposes only.

### 4. Executing with specific HTTP timeout (`GITLAB_HTTP_REQUEST_TIMEOUT=<number>`)

By default, all HTTP requests have a timeout configured to `10` seconds. If needed, you can change the default timeout for any number. For that, just set the `dev__default_timeout` property to any integer or float value. For example, in the command below, we're setting the timeout to `3` seconds:

```sh
export GITLAB_HTTP_REQUEST_TIMEOUT=3
stk run action -i "{\"token\": \"$stk_access_token\", \"project_name\": \"demo-$(date +%s)\", \"group_name\": \"stackspot\", \"visibility\": \"private\"}" --non-interactive .
```

For more information about Python's Request Library timeout, just read this article: [Timeouts in Python requests](https://datagy.io/python-requests-timeouts/)