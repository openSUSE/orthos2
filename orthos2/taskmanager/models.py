import datetime
import json
import logging
import sys
import threading
import time
from hashlib import sha1
from queue import Queue

from orthos2.data.models import ServerConfig
from django.db import IntegrityError, models
from django.utils import timezone
from orthos2.utils.misc import str_time_to_datetime

from . import Priority, TaskType

logger = logging.getLogger('tasks')


class BaseTask(models.Model):

    class Type:
        SINGLE = 0
        DAILY = 1

    class Meta:
        abstract = True

    name = models.CharField(
        max_length=200,
        blank=False
    )

    module = models.CharField(
        max_length=200,
        blank=False
    )

    arguments = models.TextField(
        default='[[], {}]'
    )

    hash = models.CharField(
        max_length=40,
        unique=True
    )

    priority = models.SmallIntegerField(
        choices=Priority.CHOICES,
        default=Priority.NORMAL,
        blank=False
    )

    running = models.BooleanField(
        null=False,
        default=False
    )

    updated = models.DateTimeField(
        'Updated at',
        auto_now=True
    )

    created = models.DateTimeField(
        'Created at',
        auto_now_add=True
    )

    def generate_hash(self):
        """Generate hash from name, module and arguments."""
        hash = sha1('{}{}{}'.format(
            self.name,
            self.module,
            self.arguments
        ).encode('utf-8')).hexdigest()

        return hash

    def save(self, *args, **kwargs):
        """Save task in database and sets hash before."""
        self.hash = self.generate_hash()
        super(BaseTask, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class DailyTask(BaseTask):

    class Meta:
        verbose_name = 'Daily Task'

    executed_at = models.DateTimeField(
        default=timezone.now,
        editable=False
    )

    enabled = models.BooleanField(
        default=True
    )

    type = BaseTask.Type.DAILY


class SingleTask(BaseTask):

    class Meta:
        verbose_name = 'Single Task'

    type = BaseTask.Type.SINGLE


class Task:

    def __new__(cls, *args, **kwargs):
        """Store arguments in attribtute for database store."""
        instance = super(Task, cls).__new__(cls)
        instance.__arguments = (args, kwargs)
        instance.basetask_type = None
        return instance

    def execute(self):
        """
        Execute the task.

        This wrapper is intented to catch unpredictable exceptions in order to log them in the
        log file (otherwise, exceptions only occure in terminal).
        """
        try:
            self.execute()
        except Exception as e:
            logger.exception(e)


class TaskManager:

    @staticmethod
    def add(task):
        """Add tasks to database for execution."""
        try:
            arguments = json.dumps(task._Task__arguments)
        except TypeError:
            logger.error("{}: arguments are not JSON serializable".format(
                task.__class__.__name__,
            ))
            return

        task, created = SingleTask.objects.get_or_create(
            name=task.__class__.__name__,
            module=task.__class__.__module__,
            arguments=arguments
        )
