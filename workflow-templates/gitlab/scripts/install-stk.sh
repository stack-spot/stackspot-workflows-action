#!/usr/bin/env bash

# ------------------------- CONFIGURE DEBUG -------------------------
    echo "Step [1/9] Configure DEBUG MODE.";
    if [ $debug == "true" ]; then
    export HTTP_ENABLE_DEBUG=true;
    echo -e "DEBUG HTTP MODE ENABLED";
    else
    echo -e "DEBUG HTTP MODE DISABLED";
    fi;
# --//--

# ------------------------- DOWNLOAD CLI -------------------------
    echo "Step [2/9] Download CLI";
    curl -O -s https://stk.stackspot.com/installer/linux/$workflow_config;
    chmod +x $workflow_config;
    exit_code_of_command=$?;
    if [ "$exit_code_of_command" != "0" ]; then
        exit $exit_code_of_command;
    fi;

    echo "Step [3/9] CLI init";
    ./$workflow_config init;
    rm $workflow_config;
    exit_code_of_command=$?;
    if [ "$exit_code_of_command" != "0" ]; then
        exit $exit_code_of_command;
    fi;

# - Download .env file of QA env when $workflow_config is 'stk-alpha'
    echo "Step [4/9] Download .env";
    chmod +x $CI_PROJECT_DIR/scripts/download-qa-env.sh;
    $CI_PROJECT_DIR/scripts/download-qa-env.sh $debug $workflow_config;
    exit_code_of_command=$?;
    if [ "$exit_code_of_command" != "0" ]; then
        exit $exit_code_of_command;
    fi;

    echo "Step [5/9] Upgrade CLI";
    ~/.$workflow_config/bin/$workflow_config --version;
    ~/.$workflow_config/bin/$workflow_config upgrade;

# - Add stk or stk-alpha to PATH environment variable
    echo "Step [6/9] Add CLI to PATH environment variable";
    export PATH="$PATH:~/.$workflow_config/bin";
# --//--

# -------------------- LOGIN AND USE WORKSPACE -------------------
    echo "Step [7/9] Execute login";
    echo "$workflow_config login $(echo $api_inputs | jq -r .cli_login_email) --realm $(echo $api_inputs | jq -r .cli_login_realm) --pat ...";
    $workflow_config login $(echo $api_inputs | jq -r .cli_login_email) --realm $(echo $api_inputs | jq -r .cli_login_realm) --pat $(echo $secrets | jq -r .secret_stk_login);
    exit_code_of_command=$?;
    if [ "$exit_code_of_command" != "0" ]; then
        exit $exit_code_of_command;
    fi;

    echo "Step [8/9] Use workspace";
    echo "$workflow_config $(echo $api_inputs | jq -r .use_workspace_cmd | base64 --decode)";
    $workflow_config $(echo $api_inputs | jq -r .use_workspace_cmd | base64 --decode);
    exit_code_of_command=$?;
    if [ "$exit_code_of_command" != "0" ]; then
        exit $exit_code_of_command;
    fi;
# --//--