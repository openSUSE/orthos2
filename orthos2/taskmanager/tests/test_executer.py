"""Tests for TaskExecuter.reset_stale_running_tasks()."""

from django.test import TestCase

from orthos2.taskmanager.executer import TaskExecuter
from orthos2.taskmanager.models import DailyTask, SingleTask


class ResetStaleRunningTasksTest(TestCase):
    def test_resets_stale_running_daily_task(self) -> None:
        task = DailyTask.objects.create(
            name="DailyMachineChecks",
            module="orthos2.taskmanager.tasks.daily",
            running=True,
        )

        TaskExecuter().reset_stale_running_tasks()

        task.refresh_from_db()
        assert not task.running

    def test_leaves_non_running_daily_task_alone(self) -> None:
        task = DailyTask.objects.create(
            name="DailyMachineChecks",
            module="orthos2.taskmanager.tasks.daily",
            running=False,
        )

        TaskExecuter().reset_stale_running_tasks()

        task.refresh_from_db()
        assert not task.running

    def test_resets_stale_running_single_task(self) -> None:
        task = SingleTask.objects.create(
            name="MachineCheck",
            module="orthos2.taskmanager.tasks.machinetasks",
            running=True,
        )

        TaskExecuter().reset_stale_running_tasks()

        task.refresh_from_db()
        assert not task.running

    def test_leaves_non_running_single_task_alone(self) -> None:
        task = SingleTask.objects.create(
            name="MachineCheck",
            module="orthos2.taskmanager.tasks.machinetasks",
            running=False,
        )

        TaskExecuter().reset_stale_running_tasks()

        task.refresh_from_db()
        assert not task.running
