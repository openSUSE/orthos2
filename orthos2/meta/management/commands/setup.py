import logging
import os
import pathlib
import shutil
from importlib.abc import Traversable
from importlib.resources import files
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

logger = logging.getLogger("meta")

ORTHOS2_USER = "orthos"
ORTHOS2_GROUP = "orthos"
CHOICE_ALL = "all"
CHOICE_SYSTEMD = "systemd"
CHOICE_ANSIBLE = "ansible"
CHOICE_CONFIG_LOGROTATE = "logrotate-config"
CHOICE_CONFIG_ORTHOS2 = "orthos2-config"
CHOICE_CONFIG_NGINX = "nginx-config"
CHOICE_TMPFILES = "tmpfiles"
CHOICE_LOGS = "logs"
CHOICE_ORTHOS_ADMIN = "orthos-admin"
CHOICE_ORTHOS_DATADIR = "orthos-datadir"
CHOICE_ORTHOS_SCRIPTS = "orthos-scripts"


class Command(BaseCommand):
    help = "Install files required for the application to run"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Entrypoint for adding arguments. Defines the choices and default directories.
        """
        parser.add_argument(
            "what",
            choices=[
                CHOICE_ALL,
                CHOICE_SYSTEMD,
                CHOICE_ANSIBLE,
                CHOICE_CONFIG_LOGROTATE,
                CHOICE_CONFIG_ORTHOS2,
                CHOICE_CONFIG_NGINX,
                CHOICE_TMPFILES,
                CHOICE_LOGS,
                CHOICE_ORTHOS_ADMIN,
                CHOICE_ORTHOS_DATADIR,
                CHOICE_ORTHOS_SCRIPTS,
            ],
            default=CHOICE_ALL,
            help="Chooses what files are being installed to the system. (Default: %s)"
            % CHOICE_ALL,
        )
        parser.add_argument(
            "--buildroot",
            type=pathlib.Path,
            default=None,
            help="This is prefixing all directory options with the given path",
        )
        parser.add_argument(
            "--directory-orthos2-config", type=pathlib.Path, default="/etc/orthos2"
        )
        parser.add_argument(
            "--directory-logrotate-config",
            type=pathlib.Path,
            default="/etc/logrotate.d",
        )
        parser.add_argument(
            "--directory-nginx-config", type=pathlib.Path, default="/etc/nginx/conf.d"
        )
        parser.add_argument(
            "--directory-logs", type=pathlib.Path, default="/var/log/orthos2"
        )
        parser.add_argument(
            "--directory-data", type=pathlib.Path, default="/var/lib/orthos2"
        )
        parser.add_argument(
            "--directory-tmpfiles", type=pathlib.Path, default="/usr/lib/tmpfiles.d"
        )
        parser.add_argument(
            "--directory-exec", type=pathlib.Path, default="/usr/lib/orthos2"
        )
        parser.add_argument(
            "--directory-unitpath", type=pathlib.Path, default="/usr/lib/systemd/system"
        )
        parser.add_argument("--directory-bindir", type=pathlib.Path, default="/usr/bin")
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing files (default is False)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Entrypoint for Django to execute the management command.
        """
        buildroot = options["buildroot"]
        if buildroot is None and os.getuid() != 0:
            self.stderr.write(
                "The setup command must be run as root (or a buildroot must be set)."
            )
            return
        what = options["what"]
        overwrite = options["overwrite"]
        if buildroot is None:
            dir_orthos2_config = options["directory_orthos2_config"]
            dir_logrotate_config = options["directory_logrotate_config"]
            dir_nginx_config = options["directory_nginx_config"]
            dir_logs = options["directory_logs"]
            dir_orthos2_data = options["directory_data"]
            dir_tmpfiles = options["directory_tmpfiles"]
            dir_exec = options["directory_exec"]
            dir_unitpath = options["directory_unitpath"]
            dir_bindir = options["directory_bindir"]
        else:
            self.stdout.write(f"Buildroot: {buildroot}")
            self.stdout.write("Prefixing buildroot to path options.")
            dir_orthos2_config = buildroot / str(
                options["directory_orthos2_config"]
            ).lstrip("/")
            dir_logrotate_config = buildroot / str(
                options["directory_logrotate_config"]
            ).lstrip("/")
            dir_nginx_config = buildroot / str(
                options["directory_nginx_config"]
            ).lstrip("/")
            dir_logs = buildroot / str(options["directory_logs"]).lstrip("/")
            dir_orthos2_data = buildroot / str(options["directory_data"]).lstrip("/")
            dir_tmpfiles = buildroot / str(options["directory_tmpfiles"]).lstrip("/")
            dir_exec = buildroot / str(options["directory_exec"]).lstrip("/")
            dir_unitpath = buildroot / str(options["directory_unitpath"]).lstrip("/")
            dir_bindir = buildroot / str(options["directory_bindir"]).lstrip("/")
            # Create base paths as they don't exist in the case of a buildroot
            dir_unitpath.mkdir(parents=True)
            dir_logrotate_config.mkdir(parents=True)
            dir_nginx_config.mkdir(parents=True)
            dir_tmpfiles.mkdir(parents=True)
            dir_logs.mkdir(parents=True)
            dir_orthos2_data.mkdir(parents=True)
        if what == CHOICE_ALL:
            self.install_systemd(dir_unitpath, overwrite=overwrite)
            self.install_ansible(dir_exec, overwrite=overwrite)
            self.install_logrotate(dir_logrotate_config, overwrite=overwrite)
            self.install_orthos2_config(dir_orthos2_config, overwrite=overwrite)
            self.install_nginx_config(dir_nginx_config, overwrite=overwrite)
            self.install_tmpfiles(dir_tmpfiles, overwrite=overwrite)
            self.install_logs(dir_logs)
            self.install_orthos2_admin(dir_bindir, overwrite=overwrite)
            self.install_orthos2_data(dir_orthos2_data)
            self.install_orthos2_scripts(dir_exec, overwrite=overwrite)
        elif what == CHOICE_SYSTEMD:
            self.install_systemd(dir_unitpath, overwrite=overwrite)
        elif what == CHOICE_ANSIBLE:
            self.install_ansible(dir_exec, overwrite=overwrite)
        elif what == CHOICE_CONFIG_LOGROTATE:
            self.install_logrotate(dir_logrotate_config, overwrite=overwrite)
        elif what == CHOICE_CONFIG_ORTHOS2:
            self.install_orthos2_config(dir_orthos2_config, overwrite=overwrite)
        elif what == CHOICE_CONFIG_NGINX:
            self.install_nginx_config(dir_nginx_config, overwrite=overwrite)
        elif what == CHOICE_TMPFILES:
            self.install_tmpfiles(dir_tmpfiles, overwrite=overwrite)
        elif what == CHOICE_LOGS:
            self.install_logs(dir_logs)
        elif what == CHOICE_ORTHOS_ADMIN:
            self.install_orthos2_admin(dir_bindir, overwrite=overwrite)
        elif what == CHOICE_ORTHOS_DATADIR:
            self.install_orthos2_data(dir_orthos2_data)
        elif what == CHOICE_ORTHOS_SCRIPTS:
            self.install_orthos2_scripts(dir_exec, overwrite=overwrite)
        else:
            self.stdout.write(f"Unknown choice: {what}!")

    def install_orthos2_admin(self, directory: pathlib.Path, overwrite: bool) -> None:
        """
        This creates the Orthos 2 wrapper script that is used to execute management commands.
        """
        self.stdout.write(f"Creating Orthos 2 administration script at: {directory}")
        source_file = (
            files("orthos2.meta.data").joinpath("bin").joinpath("orthos-admin")
        )
        self.__install_single_file(source_file, directory, overwrite=overwrite)

    def install_orthos2_config(
        self, directory: pathlib.Path, overwrite: bool = False
    ) -> None:
        """
        This creates the directory that Orthos 2 needs to store the additional configuration files,
        for Django (as we want to take the defaults from our built-in settings.py file).
        """
        self.stdout.write(
            f"Creating Orthos 2 configuration directory and files in: {directory}"
        )
        directory.mkdir(exist_ok=True)
        source_file = files("orthos2.meta.data").joinpath("config").joinpath("settings")
        self.__install_single_file(source_file, directory, overwrite=overwrite)

    def install_nginx_config(
        self, directory: pathlib.Path, overwrite: bool = False
    ) -> None:
        """
        This creates the default Nginx configuration file that we are maintaining upstream.
        """
        self.stdout.write(f"Creating Nginx configuration file at: {directory}")
        source_file = (
            files("orthos2.meta.data").joinpath("nginx").joinpath("orthos2_nginx.conf")
        )
        self.__install_single_file(source_file, directory, overwrite=overwrite)

    def install_orthos2_data(self, directory: pathlib.Path) -> None:
        """
        This creates the needed directories that Orthos 2 expects at runtime to exist.
        """
        self.stdout.write(f"Creating Orthos2 data directory at: {directory}")
        directory.mkdir(exist_ok=True)
        (directory / ".ssh").mkdir()
        (directory / "archiv").mkdir()
        (directory / "database").mkdir()
        (directory / "orthos-vm-images").mkdir()

    def install_orthos2_scripts(
        self, directory: pathlib.Path, overwrite: bool = False
    ) -> None:
        self.stdout.write(f"Creating Orthos 2 scripts at: {directory}")
        directory.mkdir(exist_ok=True)
        target_directory = directory / "scripts"
        target_directory.mkdir(exist_ok=True)
        source_directory = files("orthos2.meta.data").joinpath("scripts")
        self.__install_directory(
            source_directory, target_directory, overwrite=overwrite
        )

    def install_ansible(self, directory: pathlib.Path, overwrite: bool = False) -> None:
        """
        This creates the Ansible playbook data and templates that Orthos 2 uses internally.
        """
        self.stdout.write(f"Creating Ansible Files and Directories at: {directory}")
        directory.mkdir(exist_ok=True)
        target_directory = directory / "ansible"
        target_directory.mkdir(exist_ok=True)
        source_directory = files("orthos2.meta.data").joinpath("ansible")
        self.__install_directory(
            source_directory, target_directory, overwrite=overwrite
        )

    def install_systemd(self, directory: pathlib.Path, overwrite: bool = False) -> None:
        """
        This creates the systemd unit files for Orthos 2 that allow it to run in the background.
        """
        self.stdout.write(f"Creating systemd unit files for Orthos 2 at: {directory}")
        source_directory = files("orthos2.meta.data").joinpath("service")
        self.__install_directory(source_directory, directory, overwrite=overwrite)

    def install_logrotate(
        self, directory: pathlib.Path, overwrite: bool = False
    ) -> None:
        """
        This creates the configuration file for logrotate that prevents the log from growing infinitely.
        """
        self.stdout.write(
            f"Creating logrotate configuration file for Orthos 2 at: {directory}"
        )
        source_file = (
            files("orthos2.meta.data").joinpath("logrotate").joinpath("orthos2")
        )
        self.__install_single_file(source_file, directory, overwrite=overwrite)

    def install_tmpfiles(
        self, directory: pathlib.Path, overwrite: bool = False
    ) -> None:
        """
        This creates the configuration for Orthos 2 to store the results of the Ansible playbook.
        Assumes parent directory exists.
        """
        self.stdout.write(
            f"Installing temporary directory configuration for Orthos 2 at: {directory}"
        )
        source_file = (
            files("orthos2.meta.data").joinpath("tmpfiles.d").joinpath("orthos2.conf")
        )
        self.__install_single_file(source_file, directory, overwrite=overwrite)

    def install_logs(self, directory: pathlib.Path):
        """
        This creates the directory for file-based logging in Orthos 2.
        """
        self.stdout.write(f"Creating directory for Orthos 2 logfiles: {directory}")
        directory.mkdir(mode=0o755, exist_ok=True)
        # shutil.chown(directory, ORTHOS2_USER, ORTHOS2_GROUP)

    def __install_directory(
        self,
        source_directory: Traversable,
        target_directory: pathlib.Path,
        overwrite: bool = False,
    ) -> None:
        """
        Install a given directory recursively as-is.
        """
        for file in source_directory.iterdir():
            if file.is_dir():
                target_directory_nested = target_directory / file.name
                target_directory_nested.mkdir(mode=0o755, exist_ok=True)
                self.stdout.write(
                    f"Creating nested directory {target_directory_nested}"
                )
                self.__install_directory(file, target_directory_nested, overwrite)
                continue
            self.__install_single_file(file, target_directory, overwrite)

    def __install_single_file(
        self,
        source_file: Traversable,
        target_directory: pathlib.Path,
        overwrite: bool = False,
    ) -> None:
        target_file = target_directory / source_file.name
        if target_file.exists() and not overwrite:
            # Only overwrite files if explicitly asked to do so.
            self.stdout.write(
                f"Skipping installation of already existing file {target_file}."
            )
            return
        self.stdout.write(f"Installing {target_file}")
        source_file_content = source_file.read_text(encoding="UTF-8")
        target_file.touch(mode=0o644, exist_ok=overwrite)
        target_file.write_text(source_file_content)
