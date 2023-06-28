#!/usr/bin/env bash
debug=$1;
workflow_config=$2;
plugin_name=$3;
plugin_inputs=$4;
plugin_connection_interfaces=$5;

_print_message_if_debug_enabled(){
  if [ $debug == "true" ]; then
    echo -e $1
  fi;
}
_print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode Plugin name$two_dots_unicode $u_cyan$plugin_name";

args=();
connectors=()
if [ -z "$plugin_connection_interfaces" ] || [ "$plugin_connection_interfaces" == "null" ]; then
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode no connection-interfaces found";
else
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode plugin_connection_interfaces $plugin_connection_interfaces";

    for json_object in $(echo "$plugin_connection_interfaces" | jq -c '.[]'); do
        name=$(echo "$json_object" | jq -r '.name')
        type=$(echo "$json_object" | jq -r '.type')
        conn="--connectors.$type $name"
        connectors+=("$conn")
    done

    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode Concatened Conns $concatened_conn";
fi;

concatened_conn=$(IFS=' ' && echo "${connectors[*]}")

if [ -z "$plugin_inputs" ] || [ "$plugin_inputs" == "null" ]; then
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode no inputs-json found.";
else
    args+=("--inputs-json" "$(echo $plugin_inputs)");
    plugin_inputs_print=$(echo $plugin_inputs | jq -Rc);
    _print_message_if_debug_enabled "$green➤ DEBUG$two_dots_unicode '--inputs-json $plugin_inputs_print'";
fi;

echo -e "$green⚡ Applying Plugin $u_cyan$plugin_name\n";

echo -e $yellow $workflow_config apply plugin $plugin_name --skip-warning $(echo "${args[@]}") $concatened_conn "\n";
$workflow_config apply plugin $plugin_name --skip-warning "${args[@]}" $concatened_conn;
exit_code_of_command=$?;
if [ "$exit_code_of_command" != "0" ]; then
    echo -e "\Apply plugin failed$two_dots_unicode $plugin_name";
    echo -e "EXIT CODE$two_dots_unicode $exit_code_of_command"; 
    exit $exit_code_of_command;
fi;

echo -e "\n$green✓ Plugin applied successfully"