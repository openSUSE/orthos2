import logging
import os

from data.models import ServerConfig
from taskmanager.models import Task
from utils.ssh import SSH

logger = logging.getLogger('tasks')


class RegenerateSerialConsole(Task):
    """Regenerate the cscreen configuration for a specific serial console server."""

    def __init__(self, fqdn):
        self.fqdn = fqdn

    def execute(self):
        """Execute the task."""
        from data.models import Machine, SerialConsole

        if not ServerConfig.objects.bool_by_key('orthos.debug.serialconsole.write'):
            logger.warning("Disabled: set 'orthos.debug.serialconsole.write' to 'true'")
            return

        try:
            cscreen_server = Machine.objects.get(fqdn=self.fqdn)
        except Machine.DoesNotExist:
            logger.warning("Serial console server does not exist: {}".format(self.fqdn))

        conn = None
        try:
            conn = SSH(cscreen_server.fqdn)
            conn.connect()

            stdout, stderr, exitstatus = conn.execute('sudo touch /etc/cscreenrc_allow_update')

            if exitstatus != 0:
                raise Exception("Couldn't lock cscreen ('touch /etc/cscreenrc_allow_update')")

            new_content = ''
            for serialconsole in SerialConsole.cscreen.get(cscreen_server):
                new_content += serialconsole.get_comment_record() + '\n'
                new_content += serialconsole.get_command_record() + '\n'

            screenrc_file = '/etc/cscreenrc'

            # create `/etc/cscreenrc` if it doesn't exist
            stdout, stderr, exitstatus = conn.execute('[ -e "{}"]'.format(screenrc_file))

            orthos_inline_begin = ServerConfig.objects.by_key('orthos.configuration.inline.begin')
            orthos_inline_end = ServerConfig.objects.by_key('orthos.configuration.inline.end')

            if exitstatus != 0:
                stdout, stderr, exitstatus = conn.execute(
                    'echo "{}\n{}" > {}'.format(
                        orthos_inline_begin,
                        screenrc_file,
                        orthos_inline_end
                    )
                )

            if exitstatus != 0:
                raise Exception("Couldn't create CScreen file ('{}')".format(screenrc_file))

            # Save backup file which is used later by an invoked script
            # to determine the changes and update the running screen
            # session (add, remove or restart modified entries).
            stdout, stderr, exitstatus = conn.execute(
                'sudo cp {} {}.old'.format(screenrc_file, screenrc_file)
            )

            cscreen = conn.get_file(screenrc_file, 'r')
            buffer = ''

            in_replace = False
            for line in cscreen.readlines():
                if not in_replace and line.startswith(orthos_inline_begin):
                    buffer += line + new_content
                    in_replace = True
                elif in_replace and line.startswith(orthos_inline_end):
                    buffer += line
                    in_replace = False
                elif not in_replace:
                    buffer += line

            cscreen.close()

            cscreen = conn.get_file(screenrc_file, 'w')
            buffer = buffer.strip('\n')
            print(buffer, file=cscreen)
            cscreen.close()

            stdout, stderr, exitstatus = conn.execute('sudo /usr/bin/cscreen -u')
            logger.info("CScreen update exited with: {}".format(exitstatus))

            stdout, stderr, exitstatus = conn.execute('sudo rm -f /etc/cscreenrc_allow_update')

            if exitstatus != 0:
                raise Exception("Couldn't unlock CScreen ('rm /etc/cscreenrc_allow_update')")

        except SSH.Exception as exception:
            logger.error(exception)
        except IOError as exception:
            logger.error(exception)
        finally:
            if conn:
                conn.close()
