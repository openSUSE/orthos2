import json
import logging
from datetime import datetime
from hashlib import sha1
from typing import Any

from django.db import models
from django.utils import timezone

from . import Priority

logger = logging.getLogger("tasks")


class BaseTask(models.Model):
    class Type:
        SINGLE = 0
        DAILY = 1

    class Meta:  # type: ignore
        # pyright disable in inherited Tasks due to https://github.com/microsoft/pylance-release/issues/3814
        abstract = True

    name: "models.CharField[str, str]" = models.CharField(max_length=200, blank=False)

    module: "models.CharField[str, str]" = models.CharField(max_length=200, blank=False)

    arguments: "models.TextField[str, str]" = models.TextField(default="[[], {}]")

    hash: "models.CharField[str, str]" = models.CharField(max_length=40, unique=True)

    priority: "models.SmallIntegerField[int, int]" = models.SmallIntegerField(
        choices=Priority.CHOICES,
        default=Priority.NORMAL,
        blank=False,
    )

    running: "models.BooleanField[bool, bool]" = models.BooleanField(
        null=False,
        default=False,
    )

    updated: "models.DateTimeField[datetime, datetime]" = models.DateTimeField(
        "Updated at",
        auto_now=True,
    )

    created: "models.DateTimeField[datetime, datetime]" = models.DateTimeField(
        "Created at",
        auto_now_add=True,
    )

    def generate_hash(self) -> str:
        """Generate hash from name, module and arguments."""
        hash = sha1(
            "{}{}{}".format(self.name, self.module, self.arguments).encode("utf-8")
        ).hexdigest()

        return hash

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save task in database and sets hash before."""
        self.hash = self.generate_hash()
        super(BaseTask, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class DailyTask(BaseTask):
    class Meta:  # type: ignore
        verbose_name = "Daily Task"

    executed_at: "models.DateTimeField[datetime, datetime]" = models.DateTimeField(
        default=timezone.now,
        editable=False,
    )

    enabled: "models.BooleanField[bool, bool]" = models.BooleanField(default=True)

    type = BaseTask.Type.DAILY


class SingleTask(BaseTask):
    class Meta:  # type: ignore
        verbose_name = "Single Task"

    type = BaseTask.Type.SINGLE


class Task:
    def __new__(cls, *args: Any, **kwargs: Any) -> "Task":
        """Store arguments in attribute for database store."""
        instance = super(Task, cls).__new__(cls)
        instance.__arguments = (args, kwargs)  # type: ignore
        instance.basetask_type = None  # type: ignore
        return instance

    def execute(self) -> None:
        """
        Execute the task.

        This wrapper is intended to catch unpredictable exceptions in order to log them in the
        log file (otherwise, exceptions only occurs in terminal).
        """
        try:
            self.execute()
        except Exception as e:
            logger.exception(e)


class TaskManager:
    @staticmethod
    def add(task: Task) -> None:
        """Add tasks to database for execution."""
        try:
            arguments = json.dumps(task._Task__arguments)  # type: ignore
        except TypeError:
            logger.exception(
                "%s: arguments are not JSON serializable", task.__class__.__name__
            )
            return

        SingleTask.objects.get_or_create(
            name=task.__class__.__name__,
            module=task.__class__.__module__,
            arguments=arguments,
        )
