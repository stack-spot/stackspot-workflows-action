#!/usr/bin/env bash
debug=$1;
bitbucket_clone_dir=$2;
workflow_config=$3;
actions=$4;
secret_git_token=$5;
workspace_name=$6
name=$7
description=$8;

chmod +x $bitbucket_clone_dir/scripts/run-action.sh;

for action in $(echo $actions | jq -r '.[] | @base64'); do 
    _jq() {
        echo "${action}" | base64 --decode | jq ${1} "${2}";
    }

    action_name=$(_jq -r '.name');
    inputs=$(_jq -c '.inputs');
    createRepo=$(_jq -r '.create_repo')

    if $createRepo; then
        inputsRepo=$(echo "{\"org\": \"$workspace_name\",\"token\": \"$secret_git_token\", \"name\": \"$name\", \"description\": \"$description\"}")
        inputs=$(echo "$inputsRepo" "$inputs" | jq -cs add)
    fi
    
    $bitbucket_clone_dir/scripts/run-action.sh "$debug" "$workflow_config" "$action_name" "" "$inputs" "";

    exit_code_of_command=$?;
    if [ "$exit_code_of_command" != "0" ]; then
        exit $exit_code_of_command;
    fi
    echo -e "\n\n\n";
done