import logging
import signal
from types import FrameType
from typing import Any, Optional

from django.core.management.base import BaseCommand, CommandParser

from orthos2.taskmanager.executer import TaskExecuter

logger = logging.getLogger("tasks")
taskexecuter = TaskExecuter()


def handler(signal: int, frame: Optional[FrameType]):
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
