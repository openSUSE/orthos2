import logging
from typing import List, TextIO

from orthos2.data.models import Domain, ServerConfig
from orthos2.taskmanager.models import Task
from orthos2.utils.ssh import SSH

logger = logging.getLogger("tasks")


class RegenerateSerialConsole(Task):
    """Regenerate the cscreen configuration for a specific serial console server."""

    def __init__(self, fqdn: str) -> None:
        self.fqdn = fqdn

    def execute(self) -> None:
        """Execute the task."""
        from orthos2.data.models import Machine

        if not ServerConfig.get_server_config_manager().bool_by_key(
            "orthos.debug.serialconsole.write"
        ):
            logger.warning("Disabled: set 'orthos.debug.serialconsole.write' to 'true'")
            return

        try:
            _cscreen_server = Machine.objects.get(fqdn=self.fqdn)
        except Machine.DoesNotExist:
            logger.warning("Serial console server does not exist: %s", self.fqdn)

        conn = None
        try:
            conn = SSH(self.fqdn)
            conn.connect(user="_cscreen")

            new_content = ""
            # domains served by this cscreen server:
            domains = Domain.objects.filter(cscreen_server__fqdn=self.fqdn)
            machines: List[Machine] = []
            for domain in domains:
                machines += domain.machine_set.all()

            # logger.debug("Creating serial console for %s" % machines)
            consoles = [
                machine.serialconsole
                for machine in machines
                if hasattr(machine, "serialconsole")
            ]
            for serialconsole in consoles:
                new_content += serialconsole.get_comment_record() + "\n"
                new_content += serialconsole.get_command_record() + "\n"

            screenrc_file = "/etc/cscreenrc"

            orthos_inline_begin = ServerConfig.get_server_config_manager().by_key(
                "orthos.configuration.inline.begin"
            )
            orthos_inline_end = ServerConfig.get_server_config_manager().by_key(
                "orthos.configuration.inline.end"
            )

            if orthos_inline_begin is None or orthos_inline_end is None:
                raise ValueError("CScreen Inline Start and End cannot be None!")

            buffer = ""
            file_found = True
            try:
                cscreen: TextIO = conn.get_file(screenrc_file, "r")  # type: ignore
                in_replace = False
                marker_found = False

                for line in cscreen.readlines():
                    if not in_replace and line.startswith(orthos_inline_begin):
                        buffer += line + new_content
                        in_replace = True
                        marker_found = True
                    elif in_replace and line.startswith(orthos_inline_end):
                        buffer += line
                        in_replace = False
                    elif not in_replace:
                        buffer += line
                # orthos start marker was not found... Add it.
                if marker_found is False:
                    logging.info("CSCREEN: Orthos marker not found, adding...")
                    buffer += (
                        orthos_inline_begin + "\n" + new_content + orthos_inline_end
                    )

                cscreen.close()
            except IOError as e:
                _errno, _strerror = e.args
                import errno

                if _errno == errno.ENOENT:
                    file_found = False
                    logging.warning(
                        "%s:%s not found - creating...", self.fqdn, screenrc_file
                    )
                else:
                    raise e

            # Create an empty file with just markers, this will get the .old file
            # to diff against for new entries via cscreen -u
            if not file_found:
                buffer = orthos_inline_begin + "\n" + orthos_inline_end
                cscreen = conn.get_file(screenrc_file, "w")  # type: ignore
                buffer = buffer.strip("\n")
                print(buffer, file=cscreen)
                cscreen.close()
                buffer = orthos_inline_begin + "\n" + new_content + orthos_inline_end

            # Save backup file which is used later by an invoked script
            # to determine the changes and update the running screen
            # session (add, remove or restart modified entries).
            _stdout, stderr, exitstatus = conn.execute(
                "cp {} {}.old".format(screenrc_file, screenrc_file)
            )

            cscreen = conn.get_file(screenrc_file, "w")  # type: ignore
            buffer = buffer.strip("\n")
            print(buffer, file=cscreen)
            cscreen.close()

            _stdout, stderr, exitstatus = conn.execute("/usr/bin/cscreen -u")
            if exitstatus != 0:
                logger.warning(stderr)

            # Restart cscreend server
            _stdout, stderr, exitstatus = conn.execute(
                "sudo systemctl restart cscreend.service",
                timeout=30.0,
            )

            if exitstatus != 0:
                raise Exception("Couldn't restart cscreen")

            logger.info("CScreen update for %s finished", self.fqdn)
        except SSH.Exception as exception:
            logger.exception(exception)
        except IOError as exception:
            logger.exception(exception)
        finally:
            if conn:
                conn.close()
