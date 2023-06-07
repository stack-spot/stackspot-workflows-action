#!/usr/bin/env bash
debug=$1
workflow_config=$2

if [ $workflow_config = 'stk-alpha' ]; then
    curl -s https://stk-dev.stackspot.com/env/alpha-qa.env -o "alpha-qa.env";
    mv alpha-qa.env ~/.$workflow_config/.env;
    echo ".$workflow_config/.env created successfully";
    if [ $debug == "true" ]; then
        cat ~/.$workflow_config/.env;
    fi;
fi