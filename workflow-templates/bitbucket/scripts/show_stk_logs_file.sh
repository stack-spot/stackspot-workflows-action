#!/usr/bin/env bash
bitbucket_exit_code=$1
workflow_config=$2

echo "BITBUCKET_EXIT_CODE: $bitbucket_exit_code"
if [ "$bitbucket_exit_code" != "0" ]; then
    cat ~/.$workflow_config/logs/logs.log;
fi