#!/usr/bin/env bash
create_type=$1
workflow_api=$2
correlation_id=$3
token=$4

type="app-id:";
if [ "$create_type" == "infra" ]; then
    type="infra-id:"
fi;

register_id=$(cat .stk/stk.yaml | grep $type | cut -d : -f 2 | tr -d '[:space:]');
account_slug=$(echo $correlation_id | cut -d "|" -f 1);
execution_id=$(echo $correlation_id | cut -d "|" -f 4);

echo "$workflow_api/accounts/$account_slug/executions/$execution_id";
echo "{
    \"register_id\": \"${register_id}\"
}";

curl --location --request PUT "$workflow_api/accounts/$account_slug/executions/$execution_id" \
    --header "Authorization: $token" \
    --header "Content-Type: application/json" \
    --data-raw "{
        \"register_id\": \"$register_id\"
    }";