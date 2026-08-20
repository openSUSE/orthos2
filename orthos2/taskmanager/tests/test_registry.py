import importlib

from django.test import TestCase

from orthos2.taskmanager.models import Task
from orthos2.taskmanager.tasks.registry import (
    DAILY_TASK_CLASSES,
    SINGLE_TASK_CLASSES,
    TASK_CLASSES,
    daily_task_choices,
    resolve_daily_task_value,
    resolve_task_value,
    task_choices,
    task_value,
)


class RegistryTest(TestCase):
    def test_daily_and_single_task_classes_are_disjoint(self) -> None:
        """A task must be schedulable as either a SingleTask or a DailyTask, not both."""
        # Arrange & Act
        overlap = set(DAILY_TASK_CLASSES) & set(SINGLE_TASK_CLASSES)

        # Assert
        self.assertEqual(overlap, set())
        self.assertEqual(
            set(TASK_CLASSES), set(DAILY_TASK_CLASSES) | set(SINGLE_TASK_CLASSES)
        )

    def test_task_choices_round_trip_through_resolve_task_value(self) -> None:
        """Every SingleTask choice value must resolve back to its own (module, name)."""
        # Arrange & Act & Assert
        for value, _label in task_choices():
            resolved = resolve_task_value(value)
            self.assertIsNotNone(resolved)

    def test_daily_task_choices_round_trip_through_resolve_daily_task_value(
        self,
    ) -> None:
        """Every DailyTask choice value must resolve back to its own (module, name)."""
        # Arrange & Act & Assert
        for value, _label in daily_task_choices():
            resolved = resolve_daily_task_value(value)
            self.assertIsNotNone(resolved)

    def test_resolve_task_value_rejects_unknown_value(self) -> None:
        """An unknown value must not resolve as a SingleTask."""
        # Arrange & Act
        resolved = resolve_task_value("not.a.real.Task")

        # Assert
        self.assertIsNone(resolved)

    def test_resolve_daily_task_value_rejects_unknown_value(self) -> None:
        """An unknown value must not resolve as a DailyTask."""
        # Arrange & Act
        resolved = resolve_daily_task_value("not.a.real.Task")

        # Assert
        self.assertIsNone(resolved)

    def test_resolve_task_value_rejects_daily_only_task(self) -> None:
        """A daily-only task must not resolve as a SingleTask."""
        # Arrange
        value = task_value(DAILY_TASK_CLASSES[0])

        # Act
        resolved = resolve_task_value(value)

        # Assert
        self.assertIsNone(resolved)

    def test_every_registered_class_is_actually_importable(self) -> None:
        """Every registered class must be importable via its own (module, name) pair."""
        # Arrange & Act & Assert
        for cls in TASK_CLASSES:
            module = importlib.import_module(cls.__module__)
            imported = getattr(module, cls.__name__)
            self.assertIs(imported, cls)
            self.assertTrue(issubclass(imported, Task))
