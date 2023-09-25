import logging
import subprocess
import os
import sys
import shutil
import stat
from pathlib import Path

from errors import (
    WorkspaceShouldNotInUseError,
    ApplyPluginSetupRepositoryError,
)
from questionary import confirm

from provider import Provider

stk = sys.argv[0]


# This handler is necessary to make remove_stack_dir in Windows
# @see https://stackoverflow.com/questions/2656322/shutil-rmtree-fails-on-windows-with-access-is-denied
def on_delete_error(func, path, exc_info):
    # Is the error an access error?
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def check_workspace_in_use():
    logging.info("Validating workspace is use...")
    home_path = Path.home()
    stk_binary_name = Path(stk).stem
    stk_folder = Path(home_path) / f".{stk_binary_name}"
    workspace_config_path = stk_folder / "workspaces" / "workspace-config.json"

    if workspace_config_path.exists():
        should_exit_workspace = confirm(
            message="You need to be outside workspace, do you agree to exit current workspace?"
        ).unsafe_ask()
        if not should_exit_workspace:
            raise WorkspaceShouldNotInUseError()
        exit_workspace_cmd = [stk, "exit", "workspace"]
        subprocess.run(exit_workspace_cmd)


def create_workflow_files(provider: Provider):
    try:
        logging.info("Creating workflow files...")
        remove_all_files_generated_on_apply_plugin(provider)
        stk_apply_plugin_cmd = [
            stk,
            "apply",
            "plugin",
            str(provider.inputs.component_path),
            "--skip-warning",
            "--provider",
            provider.inputs.provider,
            "--alias",
            "setup-scm"
        ]
        result = subprocess.run(stk_apply_plugin_cmd)
        if result.returncode != 0:
            raise ApplyPluginSetupRepositoryError()
    finally:
        shutil.rmtree(".stk", onerror=on_delete_error, ignore_errors=True)


def remove_all_files_generated_on_apply_plugin(provider: Provider):
    workflow_template_provider_path = (
            Path(provider.inputs.component_path) / "workflow-templates" / provider.inputs.provider.lower()
    )
    workdir = os.getcwd()
    for subdir, dirs, files in os.walk(workflow_template_provider_path):
        for file in files:
            file_to_be_applied_path = Path(os.path.join(subdir, file))
            relative_path_file_to_be_applied = file_to_be_applied_path.relative_to(
                workflow_template_provider_path
            )

            file_path = Path(workdir) / relative_path_file_to_be_applied
            if file_path.exists():
                file_path.unlink(missing_ok=True)
