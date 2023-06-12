#!/usr/bin/env bash
debug=$1;
workflow_config=$2;
action_name=$3;
action_env=$4;
action_inputs=$5;
action_connection_interfaces=$6;

_print_message_if_debug_enabled(){
  if [ $debug == "true" ]; then
    echo -e $1
  fi;
}
_print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode Action name$two_dots_unicode $u_cyan$action_name";

args=();

if [ -z "$action_env" ] || [ "$action_env" == "null" ]; then
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode no env found";
else
    args+=("--env" $action_env);
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode '--env \"$action_env\"'";
fi;

if [ -z "$action_connection_interfaces" ] || [ "$action_connection_interfaces" == "null" ]; then
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode no connection-interfaces found";
else
    args+=("--connection-interfaces" "$(echo $action_connection_interfaces)");
    action_connection_interfaces_print=$(echo $action_connection_interfaces | jq -Rc);
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode '--connection-interfaces $action_connection_interfaces_print'";
fi;

if [ -z "$action_inputs" ] || [ "$action_inputs" == "null" ]; then
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode no inputs-json found.";
else
    args+=("--inputs-json" "$(echo $action_inputs)");
    action_inputs_print=$(echo $action_inputs | jq -Rc);
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode '--inputs-json $action_inputs_print'";
fi;

echo -e "$green⚡ Running Action $u_cyan$action_name\n";

echo -e $yellow $workflow_config run action $action_name --non-interactive $(echo "${args[@]}") "\n";
$workflow_config run action $action_name --non-interactive "${args[@]}";
exit_code_of_command=$?;
if [ "$exit_code_of_command" != "0" ]; then
    echo -e "\nAction failed$two_dots_unicode $action_name";
    echo -e "EXIT CODE$two_dots_unicode $exit_code_of_command"; 
    exit $exit_code_of_command;
fi;

echo -e "\n$green✓ Action executed successfully"