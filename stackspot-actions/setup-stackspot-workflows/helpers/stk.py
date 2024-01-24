import logging
import subprocess
import os
import sys
import shutil
from pathlib import Path

from helpers import util
from helpers.exceptions import ApplyPluginSetupRepositoryException


class Stk:
    @property
    def is_using_workspace(self) -> bool:
        home_path = Path.home()
        stk_binary_name = Path('stk').stem
        stk_folder = Path(home_path) / f".{stk_binary_name}"
        workspace_config_path = stk_folder / "workspaces" / "workspace-config.json"
        return workspace_config_path.exists()

    @staticmethod
    def exit_workspace():
        exit_workspace_cmd = ['stk', "exit", "workspace"]
        subprocess.run(exit_workspace_cmd)

    @staticmethod
    def create_workflow_files(component_path: str, provider: str):
        try:
            logging.info("Creating workflow files...")
            Stk.remove_all_files_generated_on_apply_plugin(component_path, provider)
            stk_apply_plugin_cmd = [
                'stk',
                "apply",
                "plugin",
                component_path,
                "--skip-warning",
                "--provider",
                provider,
                "--alias",
                "setup-scm"
            ]
            result = subprocess.run(stk_apply_plugin_cmd)
            if result.returncode != 0:
                raise ApplyPluginSetupRepositoryException()
        finally:
            shutil.rmtree(".stk", onerror=util.on_delete_error, ignore_errors=True)

    @staticmethod
    def remove_all_files_generated_on_apply_plugin(component_path: str, provider: str):
        workflow_template_provider_path = (
                Path(component_path) / "workflow-templates" / provider.lower()
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
