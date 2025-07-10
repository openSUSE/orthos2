import importlib
import json
import logging
import time
from queue import Empty as queueEmpty
from queue import Queue
from threading import Thread
from typing import TYPE_CHECKING, Dict, Tuple

from django import db
from django.db.utils import InterfaceError
from django.utils import timezone

from orthos2.data.models import ServerConfig
from orthos2.taskmanager import Priority
from orthos2.taskmanager.models import BaseTask, DailyTask, SingleTask

if TYPE_CHECKING:
    from .models import Task

logger = logging.getLogger("tasks")

PRIORITIES = [Priority.HIGH, Priority.NORMAL]


class TaskExecuter(Thread):
    """TaskExecuter pulls tasks from the database and executes them asynchrously."""

    def __init__(self) -> None:
        Thread.__init__(self)
        self._stop_execution = False
        self.daily_check_run = timezone.localtime()

        self.queue: Dict[int, Queue[BaseTask]] = {
            Priority.HIGH: Queue(),
            Priority.NORMAL: Queue(),
        }
        self.concurrency = int(
            ServerConfig.get_server_config_manager().by_key(  # type: ignore
                "tasks.concurrency.max",
                fallback="4",
            )
        )

    def get_daily_tasks(self) -> None:
        """Check for daily tasks and store them in the queue for processing."""
        now = timezone.localtime()
        today = timezone.localdate()

        dailytasks = DailyTask.objects.filter(enabled=True).order_by("priority")
        daily_execution_time = (
            ServerConfig.get_server_config_manager().get_daily_execution_time()
        )
        if daily_execution_time is None:
            logger.error("Daily Task execution time not set!")
            return
        for dailytask in dailytasks:
            if timezone.localdate(dailytask.executed_at) < today:
                if now.time() > daily_execution_time:
                    dailytask.executed_at = timezone.localtime()
                    dailytask.running = True
                    dailytask.save()
                    self.queue[dailytask.priority].put(dailytask)

    def get_single_tasks(self) -> None:
        """Get all single tasks from database and store them in the queue for processing."""
        singletasks = SingleTask.objects.filter(running=False).order_by("priority")
        for singletask in singletasks:
            singletask.running = True
            singletask.save()
            self.queue[singletask.priority].put(singletask)

    def reset_daily_task(self, hash: str) -> None:
        """Reset daily task and unset 'running' field."""
        try:
            dailytask = DailyTask.objects.get(hash=hash)
            dailytask.running = False
            dailytask.save()
        except DailyTask.DoesNotExist:
            logger.exception("Daily task not found")

    def remove_single_task(self, hash: str) -> None:
        """Remove task from database."""
        try:
            SingleTask.objects.get(hash=hash).delete()
        except SingleTask.DoesNotExist:
            logger.exception("Single task not found")

    def _check_threads(self, running_threads: Dict[str, Tuple[Thread, "Task"]]) -> None:
        for hash, values in list(running_threads.items()):
            thread = values[0]
            task = values[1]
            # check if thread has finished...
            if not thread.is_alive():
                if task.basetask_type == BaseTask.Type.SINGLE:  # type: ignore
                    self.remove_single_task(hash)
                else:
                    self.reset_daily_task(hash)
                del running_threads[hash]
                logger.debug("Thread [%s] %s exited", hash[:8], task.__class__.__name__)

    def run(self) -> None:
        """Main thread function."""
        running_threads: Dict[str, Tuple[Thread, "Task"]] = {}
        while not self._stop_execution:
            queue = None
            if len(running_threads) >= self.concurrency:
                time.sleep(0.25)
                self._check_threads(running_threads)
                continue
            try:
                self.get_single_tasks()
                self.get_daily_tasks()

                try:
                    basetask = self.queue[Priority.HIGH].get(timeout=1)
                    queue = self.queue[Priority.HIGH]
                except queueEmpty:
                    try:
                        basetask = self.queue[Priority.NORMAL].get(timeout=1)
                        queue = self.queue[Priority.NORMAL]
                    except queueEmpty:
                        continue

                try:
                    module = importlib.import_module(basetask.module)
                    TaskClass = getattr(module, basetask.name)

                    args = json.loads(basetask.arguments)[0]
                    kwargs = json.loads(basetask.arguments)[1]
                except ImportError:
                    logger.exception("Can't import task module '%s'", basetask.module)
                    self.remove_single_task(basetask.hash)
                    continue
                except AttributeError:
                    logger.exception("Unknown task class '%s'", basetask.name)
                    self.remove_single_task(basetask.hash)
                    continue
                except ValueError:
                    logger.exception("Invalid JSON arguments: %s", basetask.arguments)
                    continue

                if basetask.hash not in running_threads:
                    task = TaskClass(*args, **kwargs)

                    if isinstance(basetask, SingleTask):
                        task.basetask_type = BaseTask.Type.SINGLE
                    else:
                        task.basetask_type = BaseTask.Type.DAILY

                    # take parent execute function to catch and print exceptions in the log file
                    thread = Thread(target=super(TaskClass, task).execute)  # type: ignore
                    thread.start()

                    running_threads[basetask.hash] = (thread, task)
                    logger.debug(
                        "Thread [%s] %s:%s started...",
                        basetask.hash[:8],
                        basetask.name,
                        basetask.arguments,
                    )
            except InterfaceError:
                # InterfaceError is raised when the connection is closed from the db side.
                # Closing it in django forces the creation of a new connection for the next access.
                db.connection.close()
            except Exception as e:
                logger.exception(e)
            finally:
                if queue:
                    queue.task_done()
                self._check_threads(running_threads)

    def finish(self) -> None:
        self._stop_execution = True
