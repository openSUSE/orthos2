import logging
import os
import pwd
import signal
import sys
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

from orthos2.taskmanager.executer import TaskExecuter

logger = logging.getLogger("tasks")
taskexecuter = TaskExecuter()


def handler(signal, frame):
    taskexecuter.finish()


class Command(BaseCommand):
    help = "Run Orthos TaskManager"

    OPTIONS = (
        (("--start",), {"action": "store_true", "help": "Start Orthos TaskManager"}),
    )

    def add_arguments(self, parser: CommandParser) -> None:
        for (args, kwargs) in self.OPTIONS:
            parser.add_argument(*args, **kwargs)  # type: ignore

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args: Any, **options: Any) -> None:
        run_as_user = pwd.getpwuid(os.getuid())[0]
        if (not settings.DEBUG) and (run_as_user != settings.RUN_AS_USER):
            logger.error(
                "TaskManager needs to be run as user '%s', not '%s'! Exit.",
                settings.RUN_AS_USER,
                run_as_user,
            )
            sys.exit(1)
        logger.info("TaskManager runs as '%s'...", run_as_user)

        if options["start"]:
            signal.signal(signal.SIGTERM, handler)
            signal.signal(signal.SIGUSR1, handler)

            logger.info("Start TaskManager...")
            try:
                taskexecuter.start()
                signal.pause()
            except KeyboardInterrupt:
                pass

            logger.info("Stop TaskManager...")
            taskexecuter.finish()
            taskexecuter.join()
            logger.info("TaskManager stopped; Exit")
