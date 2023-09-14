#!/usr/bin/env bash
gitlab_job_status=$1 # Can be "success", "failed", or "canceled".
workflow_config=$2

echo "gitlab_job_status: $gitlab_job_status"
if [ "$gitlab_job_status" != "success" ]; then
    stk_log_file=~/.$workflow_config/logs/logs.log;
    echo "Printing '$stk_log_file' ($(cat $stk_log_file | wc -l) lines)";
    cat -n $stk_log_file;
fi