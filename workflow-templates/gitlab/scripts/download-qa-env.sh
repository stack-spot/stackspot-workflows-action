#!/usr/bin/env bash
debug=$1
workflow_config=$2

if [ $workflow_config = 'stk-alpha' ] || [ $workflow_config = 'stk-dev' ]; then
    env="alpha";
    if [ $workflow_config = 'stk-dev' ]; then
        env="dev"
    fi;        
    curl -s https://stk-dev.stackspot.com/env/$env-qa.env -o "$env-qa.env";
    mv $env-qa.env ~/.$workflow_config/.env;
    echo ".$workflow_config/.env created successfully";
    if [ $debug == "true" ]; then
        cat ~/.$workflow_config/.env;
    fi;
fi;