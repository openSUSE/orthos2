import datetime
from typing import Any, List

from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect  # type: ignore
from django.urls import URLPattern, re_path, reverse  # type: ignore
from django.utils.html import format_html
from django.utils.safestring import SafeString

from .models import DailyTask, SingleTask


class BaseTaskAdmin(admin.ModelAdmin):  # type: ignore
    readonly_fields = ("hash", "running", "created")
    list_display = (
        "name",
        "arguments",
        "running",
        "priority",
    )


admin.site.register(SingleTask, BaseTaskAdmin)  # type: ignore


class DailyTaskAdmin(BaseTaskAdmin):
    readonly_fields = BaseTaskAdmin.readonly_fields
    list_display = BaseTaskAdmin.list_display + (  # type: ignore
        "enabled",
        "task_actions",
    )

    # https://medium.com/@hakibenita/how-to-add-custom-action-buttons-to-django-admin-8d266f5b0d41
    def get_urls(self) -> List[URLPattern]:
        """Add custom URLs to daily task admin view."""
        urls = super(DailyTaskAdmin, self).get_urls()
        custom_urls = [
            re_path(
                r"^(?P<dailytask_id>.+)/execute/$",
                self.admin_site.admin_view(self.process_execute),  # type: ignore
                name="dailytask_execute",
            ),
            re_path(
                r"^(?P<dailytask_id>.+)/switch$",
                self.admin_site.admin_view(self.process_task_switch),  # type: ignore
                name="dailytask_switch",
            ),
        ]
        return custom_urls + urls

    def process_execute(
        self, request: HttpRequest, dailytask_id: int, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        """Execute specific daily task."""
        try:
            task = DailyTask.objects.get(pk=dailytask_id)
            if task.enabled:
                if task.running:
                    messages.warning(request, "Task is already running!")
                else:
                    task.executed_at = datetime.date.today() - datetime.timedelta(  # type: ignore
                        days=1
                    )
                    task.save()
                    messages.info(
                        request, "Executing daily task '{}'...".format(task.name)
                    )
            else:
                messages.warning(
                    request, "Daily task '{}' is disabled.".format(task.name)
                )
        except Exception as e:
            messages.error(request, str(e), extra_tags="error")

        return redirect("admin:taskmanager_dailytask_changelist")

    def process_task_switch(
        self, request: HttpRequest, dailytask_id: int, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        """Enable/disable task."""
        action = request.GET.get("action", None)

        if (action is not None) and (action in {"enable", "disable"}):
            try:
                task = DailyTask.objects.get(pk=dailytask_id)

                if action == "enable":
                    task.enabled = True
                    # prevent task from start running immediately
                    task.executed_at = datetime.datetime.now()
                elif action == "disable":
                    task.enabled = False
                    task.running = False

                task.save()
                messages.info(
                    request, "Successfully {}d task '{}'.".format(action, task.name)
                )

            except Exception as e:
                messages.error(request, str(e), extra_tags="error")

        return redirect("admin:taskmanager_dailytask_changelist")

    def task_actions(self, obj: DailyTask) -> SafeString:
        """Add buttons for custom daily task actions."""
        if obj.enabled:
            button = '<a class="button" href="{}?action=disable">Disable Task</a>'
        else:
            button = '<a class="button" href="{}?action=enable">Enable Task</a>'

        return format_html(
            '<a class="button" href="{}">Execute Now</a>&nbsp;' + button,
            reverse("admin:dailytask_execute", args=[obj.pk]),
            reverse("admin:dailytask_switch", args=[obj.pk]),
        )


admin.site.register(DailyTask, DailyTaskAdmin)  # type: ignore
