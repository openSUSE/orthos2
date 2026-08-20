"""
This module contains the shared forms to create and edit SingleTask/DailyTask objects.
"""

from typing import Any, Tuple

from django import forms

from orthos2.taskmanager.models import BaseTask, DailyTask, SingleTask
from orthos2.taskmanager.tasks.registry import (
    daily_task_choices,
    resolve_daily_task_value,
    resolve_task_value,
    task_choices,
)


class SingleTaskForm(forms.ModelForm):  # type: ignore
    """
    Form to create or edit a single task.

    Replaces the raw `module`/`name` fields with a single `task` choice field, since
    both must exactly match an importable `(module, name)` pair for the task to
    actually run (see `orthos2.taskmanager.executer.TaskExecuter.run`).
    """

    class Meta:  # type: ignore
        model = SingleTask
        fields = ["task", "arguments", "priority"]

    task = forms.ChoiceField(choices=task_choices, label="Task")

    resolve_task = staticmethod(resolve_task_value)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["task"].initial = "{}.{}".format(
                self.instance.module, self.instance.name
            )

    def clean_task(self) -> str:
        """Check whether the selected task resolves to a known (module, name) pair."""
        value = self.cleaned_data["task"]
        resolved = self.resolve_task(value)
        if resolved is None:
            raise forms.ValidationError("Unknown task.")
        self._resolved_task: Tuple[str, str] = resolved
        return value

    def save(self, commit: bool = True) -> BaseTask:
        """Split the selected task into `module`/`name` before saving."""
        self.instance.module, self.instance.name = self._resolved_task
        return super().save(commit=commit)  # type: ignore[no-any-return]


class DailyTaskForm(SingleTaskForm):
    """
    Form to create or edit a daily task.

    Only offers tasks meant to run on a recurring schedule (see
    `orthos2.taskmanager.tasks.registry.DAILY_TASK_CLASSES`) - everything else is a
    one-off task, only schedulable via `SingleTaskForm`.
    """

    class Meta:  # type: ignore
        model = DailyTask
        fields = ["task", "arguments", "priority", "enabled"]

    task = forms.ChoiceField(choices=daily_task_choices, label="Task")

    resolve_task = staticmethod(resolve_daily_task_value)
