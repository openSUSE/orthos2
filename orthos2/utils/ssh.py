import logging
import os
import socket
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import paramiko
from django.conf import settings
from paramiko import SFTPClient
from paramiko.channel import ChannelFile, ChannelStderrFile

from orthos2.data.models import Machine, ServerConfig

logger = logging.getLogger("utils")


class SSH(object):
    """Wrapper around internal SSH objects."""

    class Exception(Exception):  # type: ignore
        """Exception for SSH."""

        pass

    def __init__(self, fqdn: str) -> None:
        """
        Create a new SSH object.

        The connection is not established.
        """
        self._fqdn = fqdn
        if self._fqdn in {socket.getfqdn(), settings.SERVER_FQDN}:
            self._fqdn = "localhost"
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._sftp: Optional[SFTPClient] = None
        self._open = False
        try:
            self._machine = Machine.objects.get(fqdn=fqdn)
        except Exception:
            self._machine = None  # type: ignore

    def get_system_user_configuration(self) -> Optional[Dict[str, Any]]:
        """Return SSH configuration of system user as Paramiko dict for `connect()`."""
        ssh_configuration = paramiko.SSHConfig()
        user_configuration_file = "{}/.ssh/config".format(os.getenv("HOME"))

        if not os.path.exists(user_configuration_file):
            logger.warning(
                "Couldn't read SSH configuration: %s", user_configuration_file
            )
            return None

        with open(user_configuration_file) as f:
            try:
                ssh_configuration.parse(f)
            except Exception:
                logger.warning(
                    "Couldn't parse SSH configuration: %s", user_configuration_file
                )
                return None

        configuration: Dict[str, Any] = {}
        hostname = self._fqdn.split(".")[0]

        user_configuration = ssh_configuration.lookup(hostname)
        for keys in (
            ("user", "username"),
            ("identityfile", "key_filename"),
            ("port", "port"),
        ):
            if keys[0] in user_configuration:
                configuration[keys[1]] = user_configuration[keys[0]]

        if "proxycommand" in user_configuration:
            configuration["sock"] = paramiko.ProxyCommand(
                ssh_configuration["proxycommand"]  # type: ignore
            )

        return configuration

    def close(self) -> None:
        """Close the SSH connection and all open SFTP connections."""
        if self._sftp:
            self._sftp.close()
        self._client.close()
        self._open = False

    def connect(self, user: str = "root", timeout: Optional[int] = None) -> None:
        """
        Connect to the specified server (in SSH.__init__()).

        :param user: The user to use for connecting to the server.
        :param timeout: The timeout in seconds for the connection.
        """
        last_exception = None

        if not timeout:
            timeout = ServerConfig.ssh.get_timeout()

        # Paramiko doesn't provide address family option, use IPv4 address explicitly (=AF_INET)
        fqdn_or_ipv4 = self._fqdn
        if self._machine and self._machine.ipv4:
            fqdn_or_ipv4 = self._machine.ipv4

        configuration = {
            "hostname": fqdn_or_ipv4,
            "port": 22,
            "username": user,
            "key_filename": [],
            # paramiko wants timeout to be a float
            "timeout": float(timeout) if timeout else None,
        }

        try:
            if ServerConfig.ssh.bool_by_key("ssh.use.systemuser"):
                user_configuration = self.get_system_user_configuration()
                if user_configuration:
                    tmp = configuration.copy()
                    tmp.update(user_configuration)
                    configuration = tmp
            else:
                configuration["key_filename"] = ServerConfig.ssh.get_keys()

            self._client.connect(**configuration)  # type: ignore
            self._open = True
            return
        except socket.error as e:
            raise SSH.Exception("Socket error: {}".format(e))
        except paramiko.SSHException as e:
            last_exception = e

        raise SSH.Exception(last_exception)

    def execute(
        self, command: str, retry: bool = True, timeout: Optional[float] = None
    ) -> Tuple[Union[Iterable, ChannelFile], Union[Iterable, ChannelStderrFile], int]:
        """
        Execute the given command.

        :param command: The command to execute.
        :param retry: Set to "True" to retry the command once if it failed on the remote (default).
        :param timeout: Timeout in seconds or "None" to disable setting a timeout (default).
        :returns: A tuple containing stdout (list), stderr (list) and exit status (int).
        """
        try:
            stdout: Union[Iterable, ChannelFile]
            stderr: Union[Iterable, ChannelStderrFile]
            _stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)
            exitstatus = stdout.channel.recv_exit_status()

            stdout = stdout.readlines()
            stderr = stderr.readlines()

            stdout = stdout if stdout else []
            stderr = stderr if stderr else []

            return stdout, stderr, exitstatus

        except Exception as e:
            if retry:
                # reconnect
                self.connect()
                # avoid loops, therefore we set retry to False
                return self.execute(command, retry=False)
            else:
                raise SSH.Exception(str(e))

        except socket.timeout:
            raise SSH.Exception("Command timed out")
        except Exception:
            raise SSH.Exception("Unknown SSH exception")

    def read_file(self, filename: str) -> List[str]:
        """Read the given file contents."""
        if not self._sftp:
            self._sftp = self._client.open_sftp()
        f = self._sftp.file(filename, "r")
        retval = f.readlines()
        f.close()
        return retval

    def get_file(self, filename: str, mode: str) -> paramiko.SFTPFile:
        """Return a file-like object for filename with mode `mode`."""
        if not self._sftp:
            self._sftp = self._client.open_sftp()
        f = self._sftp.file(filename=filename, mode=mode)
        return f

    def execute_script_remote(
        self, script: str, arguments: str = ""
    ) -> Optional[Tuple[str, str, int]]:
        """
        Execute the given script on the remote side.

        Return a tuple containing stdout (list), stderr (list) and exit status (int).
        """
        retval = ("", "", 1)

        remotescript_directory = ServerConfig.ssh.get_remote_scripts_directory()
        remotescript = os.path.join(remotescript_directory, script)
        localscript = os.path.join(
            ServerConfig.ssh.get_local_scripts_directory(), script
        )

        if not self._sftp:
            self._sftp = self._client.open_sftp()

        try:
            self._sftp.stat(remotescript_directory)  # type: ignore
        except IOError:
            try:
                self._sftp.mkdir(remotescript_directory)  # type: ignore
            except IOError:
                return None

        self._sftp.put(localscript, remotescript)
        self._sftp.chmod(remotescript, 755)
        try:
            retval = self.execute("{} {}".format(remotescript, arguments))  # type: ignore
        except SSH.Exception as e:
            logger.warning(
                "Error while executing command %s on %s: %s", script, self._fqdn, str(e)
            )

        try:
            for f in self._sftp.listdir(remotescript_directory):  # type: ignore
                self._sftp.remove(os.path.join(remotescript_directory, f))  # type: ignore
            self._sftp.rmdir(remotescript_directory)  # type: ignore
        except paramiko.SSHException as e:
            logger.exception(e)
            logger.warning(
                "Error while executing command %s on %s: %s", script, self._fqdn, str(e)
            )
        except paramiko.SFTPError as e:
            logger.exception(e)
            logger.warning(
                "Error while executing command %s on %s: %s", script, self._fqdn, str(e)
            )
        except IOError as e:
            logger.exception(e)
            logger.warning(
                "Error while executing command %s on %s: %s", script, self._fqdn, str(e)
            )

        return retval

    def copy_file(self, localfile: str, remotefile: str, parents: bool = False) -> None:
        """
        Copy a local file to the remote side.

        If `parents` is true, create target directory recursively.
        """
        if not self._sftp:
            self._sftp = self._client.open_sftp()

        try:
            directory, _filename = os.path.split(remotefile)
            self._sftp.chdir(directory)
        except FileNotFoundError as e:
            if not parents:
                raise e

            directories = directory.lstrip("/").split("/")

            for i, _part in enumerate(directories):
                directory = "/" + "/".join(directories[0 : i + 1])
                try:
                    self._sftp.chdir(directory)
                except FileNotFoundError:
                    self._sftp.mkdir(directory)

        self._sftp.put(localfile, remotefile)

    def remove_file(self, remotefile: str) -> None:
        """Delete a file on the remote side."""
        if not self._sftp:
            self._sftp = self._client.open_sftp()

        self._sftp.remove(remotefile)

    def check_path(self, path: str, test: str) -> bool:
        """
        Check if the file/directory exists remotely.

        :param path: The path to test for.
        :param test: Arguments that are passed to "test".
        """
        _stdout, _stderr, exitstatus = self.execute('test {} "{}"'.format(test, path))

        if exitstatus != 0:
            return False

        return True
