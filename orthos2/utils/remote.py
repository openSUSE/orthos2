#!/usr/bin/python3

import logging

from orthos2.utils.misc import execute

logger = logging.getLogger('utils')

def single_quote(buf):
    """
    Put the whole string into single quotes and escape
    single quotes via '\'' to properly pass shell commands via ssh

    @type  buf: string
    @param buf: The string to be escaped.
    @rtype: string
    @return: The input string put in single quotes and containing quotes escaped.
    """
    buf = "'" + buf.replace("'","'\\''") + "'"
    return buf

def ssh_execute(cmd, host, user='root', log_error=True):
    """
    Get the output of a command remotly via SSH.

    @type  cmd:       string
    @param cmd:       The command to execute.
    @type  host:      string
    @type  log_error: bool
    @param log_error: If True and ssh returns an error code, the stderr is written to the log.
    @type  verbose:   bool
    @param verbose:   If True, the ssh command and stderr are written to the log.
    @param host:      The host on which the command should be executed.
    @rtype:           string
    @return:          The stdout output of the executed command.
    @rtype:           string
    @return:          The stderr output of the executed command.
    @rtype:           int
    @return:          The exit code of the executed command
    """
    ssh_command = 'ssh -o UserKnownHostsFile=/dev/null ' \
        '-o StrictHostKeyChecking=no ' \
        '-o ConnectTimeout=5 ' \
        + user + '@' + host + ' ' +  single_quote(cmd)
    (stdout, stderr, err) = execute(ssh_command)
    if (err and log_error):
        logger.warning("stderr: %s", stderr)
        logger.warning("ssh command: %s", ssh_command)
        logger.warning("stdout: %s", stdout)

    stdout = stdout.splitlines()
    stderr = stderr.splitlines()

    stdout = stdout if stdout else []
    stderr = stderr if stderr else []

    return (stdout, stderr, err)


def scp_execute(source, target, user='root'):
    """
    Copy a file via SSH without host key checking.

    @type  source:  string
    @param source:  The full path and filename of the source.
    @type  target:  string
    @param target:  The full path and filename of the target.
    @rtype:         int
    @return:        0 if everything went well.
    """
    command = 'scp -o UserKnownHostsFile=/dev/null ' \
              '-o StrictHostKeyChecking=no ' \
              '-o ConnectTimeout=5 ' \
              '{} {}@{}'.format(source, user, target)
    return execute(command)



# Test ssh code above by passing:
# cmd:  arg[0]
# host: arg[1]
if __name__ == '__main__':
    import sys
    if len(sys.argv) == 3:
        args = sys.argv[1:]
        cmd = args[0]
        host = args[1]

    # stdout, stderr, err = ssh_execute(cmd, host)
    # stdout, stderr, err = ssh_execute('/sbin/ip a', "gatria-1.arch.suse.de")
    stdout, stderr, err = scp_execute(cmd, host)
    if err:
        print ("ERROR")
        print (stderr)
    else:
        print("SUCCESS")
        print(stdout)

