debug=$1;
workflow_config=$2;
workspace_pat=$3;
workspace_name=$4
name=$5
description=$6;
create_repo_action=$7

_print_message_if_debug_enabled(){
  if [ $debug == "true" ]; then
    echo -e $1
  fi;
}

if [ -n "$create_repo_action" ]; then
    if [ -z "$workspace_pat" ] || [ "$workspace_pat" == "null" ]; then
        echo -e "$red✖ ERROR⇾ 'workspace_pat' field not found in json for 'secrets' input";
        exit 1;
    fi

    action_inputs=$(echo "$create_repo_action" | jq -cr .inputs)
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode Action Inputs$two_dots_unicode $action_inputs";

    inputs_repo=$(echo "{\"org\": \"$workspace_name\",\"token\": \"$workspace_pat\", \"name\": \"$name\", \"description\": \"$description\"}")
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode Inputs Repo$two_dots_unicode $inputs_repo";

    merged_inputs=$(echo $action_inputs $inputs_repo | jq -cs add)
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode Merged Inputs$two_dots_unicode $merged_inputs";

    parsed_inputs=$(echo "{ \"inputs\": $merged_inputs }")
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode Parsed Inputs$two_dots_unicode $parsed_inputs";

    action_create_name=$(echo $create_repo_action | jq -cM .name)
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode Action Name$two_dots_unicode $action_create_name";

    final_action=$(echo "[{ \"name\": $action_create_name, \"inputs\": $merged_inputs }]")
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode Final Action$two_dots_unicode $final_action";
    echo -e $yellow $workflow_config run actions -a "$(echo $final_action)" -e $execution_id -w before"\n";
    $workflow_config run actions -a "$(echo $final_action)" -e $execution_id -w before;

    exit_code_of_command=$?;
    if [ "$exit_code_of_command" != "0" ]; then
        echo -e "\nAction failed";
        echo -e "EXIT CODE$two_dots_unicode $exit_code_of_command"; 
        exit $exit_code_of_command;
    fi;
else
    echo -e "$green➤ DEBUG$two_dots_unicode No Action to run";
fi