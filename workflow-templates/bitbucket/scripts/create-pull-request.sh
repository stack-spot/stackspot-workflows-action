#!/usr/bin/env bash
echo "Creating Pull Request";

workspace_name=$1
repo_name=$2
workspace_pat=$3
name=$4
branch_name=$5
default_branch=$6
description=$7

pull_request_id=$(curl --location "https://api.bitbucket.org/2.0/repositories/$workspace_name/$repo_name/pullrequests" \
    --header "Accept: application/json" \
    --header "Content-Type: application/json" \
    --header "Authorization: Bearer $workspace_pat" \
    --data "{
        \"title\": \"Create $name\",
        \"source\": {
            \"branch\": {
                \"name\": \"$branch_name\"
            }
        },
        \"destination\": {
            \"branch\": {
                \"name\": \"$default_branch\"
            }
        },
        \"summary\": {
            \"raw\": \"$description\"
        }
    }" | jq .id);

echo "Created Pull Request successfully";
echo "https://bitbucket.org/$workspace_name/$repo_name/pull-requests/$pull_request_id";