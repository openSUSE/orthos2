# For test purposes:
# Execute via:
#
# python3 /usr/lib/python3.*/site-packages/orthos2/utils/remote.py <cmd> <host>
# python3 /usr/lib/python3.*/site-packages/orthos2/utils/remote.py ls gatria-1.arch.suse.de

import logging
from typing import List, Tuple

from orthos2.utils.misc import execute

logger = logging.getLogger("utils")


def single_quote(buf: str) -> str:
    """
    Put the whole string into single quotes and escape
    single quotes via '\'' to properly pass shell commands via ssh

    @type  buf: string
    @param buf: The string to be escaped.
    @rtype: string
    @return: The input string put in single quotes and containing quotes escaped.
    """
    buf = "'" + buf.replace("'", "'\\''") + "'"
    return buf


def ssh_execute(
    cmd: str, host: str, user: str = "root", log_error: bool = True
) -> Tuple[List[str], List[str], int]:
    """
    Get the output of a command remotly via SSH.

    :param cmd: The command to execute.
    :param host: The host on which the command should be executed.
    :param user: The username on the host where the command should be executed.
    :param log_error: If True and ssh returns an error code, the stderr is written to the log.
    :returns: A tuple of (stdout, stderr, return_code).
    """
    ssh_command = (
        "ssh -o UserKnownHostsFile=/dev/null "
        "-o StrictHostKeyChecking=no "
        "-o ConnectTimeout=5 " + user + "@" + host + " " + single_quote(cmd)
    )
    (stdout, stderr, err) = execute(ssh_command)
    if err and log_error:
        logger.warning("stderr: %s", stderr)
        logger.warning("ssh command: %s", ssh_command)
        logger.warning("stdout: %s", stdout)

    stdout_split = stdout.splitlines()
    stderr_split = stderr.splitlines()
    stdout_split = stdout_split if stdout_split else []
    stderr_split = stderr_split if stderr_split else []

    return stdout_split, stderr_split, err


def scp_execute(source: str, target: str, user: str = "root") -> int:
    """
    Copy a file via SSH without host key checking.

    :param source: The full path and filename of the source.
    :param target: The full path and filename of the target.
    :param user: The username used to connect to the target host.
    :returns: 0 if everything went well.
    """
    command = (
        "scp -o UserKnownHostsFile=/dev/null "
        "-o StrictHostKeyChecking=no "
        "-o ConnectTimeout=5 "
        "{} {}@{}".format(source, user, target)
    )
    return execute(command)[2]
