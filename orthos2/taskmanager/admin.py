import datetime

from django.conf.urls import url
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from . import Priority
from .models import DailyTask, SingleTask


class BaseTaskAdmin(admin.ModelAdmin):
    readonly_fields = (
        'hash',
        'running',
        'created'
    )
    list_display = (
        'name',
        'arguments',
        'running',
        'priority',
    )


admin.site.register(SingleTask, BaseTaskAdmin)


class DailyTaskAdmin(BaseTaskAdmin):
    readonly_fields = BaseTaskAdmin.readonly_fields
    list_display = BaseTaskAdmin.list_display + (
        'enabled',
        'task_actions',
    )

    # https://medium.com/@hakibenita/how-to-add-custom-action-buttons-to-django-admin-8d266f5b0d41
    def get_urls(self):
        """Add customn URLs to daily task admin view."""
        urls = super(DailyTaskAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^(?P<dailytask_id>.+)/execute/$',
                self.admin_site.admin_view(self.process_execute),
                name='dailytask_execute'
            ),
            url(
                r'^(?P<dailytask_id>.+)/switch$',
                self.admin_site.admin_view(self.process_task_switch),
                name='dailytask_switch'
            ),
        ]
        return custom_urls + urls

    def process_execute(self, request, dailytask_id, *args, **kwargs):
        """Execute specific daily task."""
        try:
            task = DailyTask.objects.get(pk=dailytask_id)
            if task.enabled:
                if task.running:
                    messages.warning(request, "Task is already running!")
                else:
                    task.executed_at = datetime.date.today() - datetime.timedelta(days=1)
                    task.save()
                    messages.info(request, "Executing daily task '{}'...".format(task.name))
            else:
                messages.warning(request, "Daily task '{}' is disabled.".format(task.name))
        except Exception as e:
            messages.error(request, str(e), extra_tags='error')

        return redirect('admin:taskmanager_dailytask_changelist')

    def process_task_switch(self, request, dailytask_id, *args, **kwargs):
        """Enable/disable task."""
        action = request.GET.get('action', None)

        if (action is not None) and (action in {'enable', 'disable'}):
            try:
                task = DailyTask.objects.get(pk=dailytask_id)

                if action == 'enable':
                    task.enabled = True
                    # prevent task from start running immediately
                    task.executed_at = datetime.datetime.now()
                elif action == 'disable':
                    task.enabled = False
                    task.running = False

                task.save()
                messages.info(request, "Successfully {}d task '{}'.".format(action, task.name))

            except Exception as e:
                messages.error(request, str(e), extra_tags='error')

        return redirect('admin:taskmanager_dailytask_changelist')

    def task_actions(self, obj):
        """Add buttons for custom daily task actions."""
        if obj.enabled:
            button = '<a class="button" href="{}?action=disable">Disable Task</a>'
        else:
            button = '<a class="button" href="{}?action=enable">Enable Task</a>'

        return format_html(
            '<a class="button" href="{}">Execute Now</a>&nbsp;' + button,
            reverse('admin:dailytask_execute', args=[obj.pk]),
            reverse('admin:dailytask_switch', args=[obj.pk])
        )


admin.site.register(DailyTask, DailyTaskAdmin)
