"""
All views that are related to "/statistics".
"""

import datetime
from datetime import timezone as tz
from typing import List

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from orthos2.data.models import Architecture, Domain, Machine, ReservationHistory


@login_required
def statistics(request: HttpRequest) -> HttpResponse:
    total = Machine.objects.all().count()

    status_ping = Machine.objects.filter(
        Q(status_ipv4=Machine.StatusIP.REACHABLE)
        | Q(status_ipv4=Machine.StatusIP.CONFIRMED)
        | Q(status_ipv6=Machine.StatusIP.REACHABLE)
        | Q(status_ipv6=Machine.StatusIP.CONFIRMED)
    ).count()
    status_ssh = Machine.objects.filter(status_ssh=True).count()
    status_login = Machine.objects.filter(status_login=True).count()

    check_ping = Machine.objects.filter(
        check_connectivity__gte=Machine.Connectivity.PING
    ).count()

    check_ssh = Machine.objects.filter(
        check_connectivity__gte=Machine.Connectivity.SSH
    ).count()

    check_login = Machine.objects.filter(
        check_connectivity__gte=Machine.Connectivity.ALL
    ).count()

    released_reservations = ReservationHistory.objects.filter(  # type: ignore
        reserved_until__gt=timezone.make_aware(
            datetime.datetime.today() - datetime.timedelta(days=2),
            timezone.get_default_timezone(),
        ),
        reserved_until__lte=timezone.make_aware(
            datetime.datetime.today(), timezone.get_default_timezone()
        ),
    )

    reserved_machines = Machine.objects.filter(
        reserved_at__gt=timezone.make_aware(
            datetime.datetime.today() - datetime.timedelta(days=2),
            timezone.get_default_timezone(),
        ),
        reserved_at__lte=timezone.make_aware(
            datetime.datetime.today(), timezone.get_default_timezone()
        ),
    )

    matrix: List[List[int]] = [[], [], [], []]

    for architecture in Architecture.objects.all():
        matrix[0].append(architecture.machine_set.count())
        matrix[1].append(architecture.machine_set.filter(reserved_by=None).count())
        matrix[2].append(architecture.machine_set.filter(status_login=True).count())
        infinite = timezone.datetime.combine(  # type: ignore
            datetime.date.max, timezone.datetime.min.time()  # type: ignore
        )
        infinite = timezone.make_aware(infinite, tz.utc)
        matrix[3].append(
            architecture.machine_set.filter(reserved_until=infinite).count()
        )

    matrix[0].append(sum(matrix[0]))
    matrix[1].append(sum(matrix[1]))
    matrix[2].append(sum(matrix[2]))
    matrix[3].append(sum(matrix[3]))

    data = {
        "total": total,
        "matrix": matrix,
        "status": {
            "labels": ["Ping", "SSH", "Login"],
            "values1": [check_ping, check_ssh, check_login],
            "values2": [status_ping, status_ssh, status_login],
            "max": total if total % 100 == 0 else total - (total % 100) + 100,
        },
        "domains": {
            "labels": list(Domain.objects.all().values_list("name", flat=True)),
            "values": [domain.machine_set.count() for domain in Domain.objects.all()],
        },
        "released_reservations": released_reservations,
        "reserved_machines": reserved_machines,
    }

    return render(
        request,
        "frontend/machines/statistics.html",
        {
            "architectures": Architecture.objects.all(),
            "data": data,
            "title": "Statistics",
        },
    )
