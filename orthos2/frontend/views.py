import datetime
import functools
import logging
import warnings

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import (REDIRECT_FIELD_NAME, authenticate,
                                 update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.urls import resolve
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render, resolve_url, reverse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import ListView

from data.exceptions import ReleaseException, ReserveException
from data.models import (Architecture, Domain, Machine, MachineGroup,
                         RemotePower, ReservationHistory, SerialConsole,
                         SerialConsoleType, ServerConfig)
from taskmanager import tasks
from taskmanager.models import TaskManager
from utils.misc import add_offset_to_date, get_random_mac_address

from .decorators import check_permissions
from .forms import (NewUserForm, PasswordRestoreForm, PreferencesForm,
                    ReserveMachineForm, SearchForm, SetupMachineForm,
                    VirtualMachineForm)

logger = logging.getLogger('views')


class MachineListView(ListView):
    model = Machine
    template_name = "machines/list.html"
    paginate_by = 50

    # login is required for all machine lists
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(MachineListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return pre-filtered query set for every machine list.

        Adminsitrative machines and administrative systems are excluded.
        """
        filters = []

        if self.request.GET.get('query'):
            filters.append(Q(fqdn__contains=self.request.GET.get('query')))

        if self.request.GET.get('arch'):
            filters.append(Q(architecture__name=self.request.GET.get('arch')))

        if self.request.GET.get('domain'):
            filters.append(Q(fqdn_domain__name=self.request.GET.get('domain')))

        if self.request.GET.get('machinegroup'):
            filters.append(Q(group__name=self.request.GET.get('machinegroup')))

        status = self.request.GET.get('status')
        if status and status == 'ping':
            filters.append(
                Q(status_ipv4=Machine.StatusIP.REACHABLE) |
                Q(status_ipv4=Machine.StatusIP.CONFIRMED) |
                Q(status_ipv6=Machine.StatusIP.REACHABLE) |
                Q(status_ipv6=Machine.StatusIP.CONFIRMED)
            )
        elif status:
            filters.append(Q(**{'status_{}'.format(status): True}))

        machines = Machine.view.get_queryset(user=self.request.user).filter(*filters)

        return machines

    def get_context_data(self, **kwargs):
        context = super(MachineListView, self).get_context_data(**kwargs)
        context['machine_list'] = self.object_list

        order_by = self.request.GET.get('order_by', None)
        order_direction = self.request.GET.get('order_direction', None)
        if order_by and order_direction in ['asc', 'desc']:
            context['machine_list'] = self.object_list.order_by(
                '{}'.format(order_by) if order_direction == 'asc' else '-{}'.format(order_by)
            )
            # hit the DB to check order_by fields and restore the queryset if something fails
            try:
                context['machine_list'] = list(context['machine_list'])
            except KeyError:
                context['machine_list'] = self.object_list

        paginator = Paginator(context['machine_list'], self.paginate_by)

        page = self.request.GET.get('page')

        try:
            machines = paginator.page(page)
        except PageNotAnInteger:
            machines = paginator.page(1)
        except EmptyPage:
            machines = paginator.page(paginator.num_pages)

        context['architectures'] = Architecture.objects.all()
        context['domains'] = Domain.objects.all()
        context['machines'] = machines
        context['machinegroups'] = MachineGroup.objects.all()
        context['paginator'] = paginator
        return context


class AllMachineListView(MachineListView):
    """`All Machines` list view."""

    def get(self, request, *args, **kwargs):
        """Redirect to `Free Machines` if a non-superuser tries to request `All Machines`."""
        if not request.user.is_superuser:
            return redirect('frontend:free_machines')

        return super(AllMachineListView, self).get(request, *args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        context['title'] = 'All Machines'
        return super(AllMachineListView, self).render_to_response(context, **response_kwargs)


class MyMachineListView(MachineListView):
    """`My Machines` list view."""

    def get_queryset(self):
        """Filter machines which are reserved by requesting user."""
        machines = super(MyMachineListView, self).get_queryset()
        return machines.filter(reserved_by=self.request.user)

    def render_to_response(self, context, **response_kwargs):
        context['title'] = 'My Machines'
        context['view'] = 'my'
        return super(MyMachineListView, self).render_to_response(context, **response_kwargs)


class FreeMachineListView(MachineListView):
    """`Free Machines` list view."""

    def get_queryset(self):
        """Filter machines which are NOT reserved and NO dedicated VM hosts."""
        machines = super(FreeMachineListView, self).get_queryset()
        return machines.filter(
            reserved_by=None,
            vm_dedicated_host=False
        )

    def render_to_response(self, context, **response_kwargs):
        context['title'] = 'Free Machines'
        context['view'] = 'free'
        return super(FreeMachineListView, self).render_to_response(context, **response_kwargs)


class VirtualMachineListView(MachineListView):
    """`Virtual Machines` list view."""

    def get_queryset(self):
        """Filter machines which are capable to run VMs and which are dedicated VM hosts."""
        machines = super(VirtualMachineListView, self).get_queryset()
        return machines.filter(
            vm_capable=True,
            vm_dedicated_host=True
        )

    def render_to_response(self, context, **response_kwargs):
        """Add VMs running already."""
        context['title'] = 'Virtual Machines'
        context['view'] = 'virtual'

        vm_hosts = context['machines']
        machines = []

        # collect VMs of respective VM host
        for vm_host in vm_hosts:
            machines.append(vm_host)
            vm_machines = list(vm_host.get_virtual_machines())
            if vm_machines:
                machines.extend(vm_machines)

        context['machines'] = machines

        return super(VirtualMachineListView, self).render_to_response(context, **response_kwargs)


@login_required
@check_permissions()
def machine(request, id):
    try:
        machine = Machine.objects.get(pk=id)
        machine.enclosure.fetch_location(machine.pk)
    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist.")
        return redirect('machines')

    return render(
        request,
        'machines/detail/overview.html', {
            'machine': machine,
            'title': 'Machine'
        }
    )


@login_required
def pci(request, id):
    try:
        machine = Machine.objects.get(pk=id)
        machine.enclosure.fetch_location(machine.pk)
        return render(
            request,
            'machines/detail/pci.html', {
                'machine': machine,
                'title': 'lspci'
            }
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def cpu(request, id):
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            'machines/detail/cpu.html', {
                'machine': machine,
                'title': 'CPU'
            }
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def networkinterfaces(request, id):
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            'machines/detail/networkinterfaces.html', {
                'machine': machine,
                'title': 'Network Interfaces'
            }
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def installations(request, id):
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            'machines/detail/installations.html', {
                'machine': machine,
                'title': 'Installations'
            }
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def usb(request, id):
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            'machines/detail/usb.html', {
                'machine': machine,
                'title': 'USB'
            }
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def scsi(request, id):
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            'machines/detail/scsi.html', {
                'machine': machine,
                'title': 'SCSI'
            }
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def virtualization(request, id):
    try:
        machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")

    if machine.virtualization_api is None:
        return HttpResponse(status=501, content="No virtualization API available!")

    return render(
        request,
        'machines/detail/virtualization.html', {
            'machine': machine,
            'title': 'Virtualization'
        }
    )


@login_required
def virtualization_add(request, id):
    try:
        machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")

    if machine.virtualization_api is None:
        return HttpResponse(status=501, content="No virtualization API available!")

    if request.method == 'GET':
        form = VirtualMachineForm(virtualization_api=machine.virtualization_api)

    else:
        form = VirtualMachineForm(request.POST, virtualization_api=machine.virtualization_api)

        if form.is_valid():
            try:
                vm = machine.virtualization_api.create(**form.cleaned_data)

                vm.reserve(
                    reason='VM of {}'.format(request.user),
                    until=add_offset_to_date(30),
                    user=request.user
                )
                messages.success(request, "Virtual machine '{}' created.".format(vm.fqdn))

                return redirect('frontend:detail', id=vm.pk)

            except Exception as exception:
                logger.exception(exception)
                messages.error(request, exception)
                return redirect('frontend:machines')

    return render(
        request,
        'machines/detail/virtualization_add.html', {
            'form': form,
            'machine': machine,
            'title': 'Virtualization'
        }
    )


@login_required
def misc(request, id):
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            'machines/detail/miscellaneous.html', {
                'machine': machine,
                'title': 'Miscellaneous'
            }
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
@check_permissions()
def machine_reserve(request, id):
    try:
        machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        messages.error(request, 'Machine does not exist!')
        return redirect('fronted:machines')

    if request.method == 'GET':
        form = ReserveMachineForm(
            reason=machine.reserved_reason,
            until=machine.reserved_until
        )

    else:
        form = ReserveMachineForm(request.POST)

        if form.is_valid():
            reason = form.cleaned_data['reason']
            until = form.cleaned_data['until']

            try:
                machine.reserve(
                    reason,
                    until,
                    user=request.user
                )
                messages.success(request, "Machine successfully reserved.")
            except Exception as exception:
                messages.error(request, exception)

            return redirect('frontend:detail', id=id)

    return render(
        request,
        'machines/reserve.html', {
            'form': form,
            'machine': machine,
            'title': 'Reserve Machine'
        }
    )


@login_required
@check_permissions()
def machine_release(request, id):
    try:
        machine = Machine.objects.get(pk=id)

        try:
            machine.release(user=request.user)
            messages.success(request, 'Machine successfully released.')

            if machine.is_virtual_machine():
                if machine.hypervisor and (machine.hypervisor.virtualization_api is not None):
                    return redirect('frontend:machines')

        except Exception as exception:
            logger.exception(exception)
            messages.error(request, exception)

        return redirect('frontend:detail', id=id)

    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist!")
        return redirect('frontend:machines')


@login_required
def history(request, id):
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            'machines/detail/history.html', {
                'machine': machine,
                'title': 'Reservation History'
            }
        )
    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist!")
        return redirect('forntend:machines')


@login_required
@check_permissions()
def rescan(request, id):
    try:
        machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist!")
        return redirect('frontend:machines')

    if request.GET.get('action'):
        try:
            machine.scan(request.GET.get('action'))
            messages.info(request, "Rescanning machine - this can take some seconds...")
        except Exception as exception:
            messages.error(request, exception)

    return redirect('frontend:detail', id=id)


@login_required
@check_permissions()
def setup(request, id):
    try:
        machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        messages.error(request, 'Machine does not exist!')
        return redirect('frontend:machines')

    if request.method == 'GET':
        if not machine.has_remotepower():
            messages.warning(
                request,
                "This machine has no remote power - a manuall reboot may be required."
            )
        form = SetupMachineForm(machine=machine)

    else:

        form = SetupMachineForm(request.POST, machine=machine)

        if form.is_valid():
            choice = form.cleaned_data['setup']

            machinegroup = None
            if machine.group and not machine.group.setup_use_architecture:
                machinegroup = machine.group.name

            valid = machine.fqdn_domain.is_valid_setup_choice(
                choice,
                machine.architecture.name,
                machinegroup=machinegroup
            )
            if not valid:
                messages.error(request, "Unknown choice '{}'!".format(choice))
                return redirect('frontend:detail', id=id)

            try:
                result = machine.setup(choice)

                if result:
                    messages.success(request, "Setup '{}' initialized.".format(choice))
                else:
                    messages.warning(
                        request,
                        "Machine has no setup capability! Please contact '{}'.".format(
                            machine.get_support_contact()
                        )
                    )

            except Exception as exception:
                messages.error(request, exception)

        return redirect('frontend:detail', id=id)

    return render(
        request,
        'machines/setup.html', {
            'form': form,
            'machine': machine,
            'title': 'Setup Machine'
        }
    )


@login_required
def console(request, id):
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            'machines/detail/console.html', {
                'machine': machine,
                'port': ServerConfig.objects.by_key('websocket.cscreen.port'),
                'title': 'Serial Console'
            }
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


def users_create(request):
    if request.method == 'GET':
        form = NewUserForm()
    else:
        if not ServerConfig.objects.bool_by_key('auth.account.creation'):
            messages.error(request, "Account creation is disabled!")
            return redirect('frontend:login')

        form = NewUserForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['login']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            new_user = User.objects.create_user(
                username=username,
                email=email.lower(),
                password=password
            )
            new_user.save()

            new_user = authenticate(username=username, password=password)
            auth_login(request, new_user)

            return redirect('frontend:machines')

    return render(
        request,
        'registration/new.html', {
            'form': form,
            'title': 'Create User'
        }
    )


def users_password_restore(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id', None)
        username = None

        if user_id is not None:
            try:
                user = User.objects.get(pk=user_id)
                username = user.username
            except Exception:
                pass

        form = PasswordRestoreForm(username=username)

    else:
        form = PasswordRestoreForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            username = form.cleaned_data['login']

            try:
                user = User.objects.get(email=email, username=username)
            except User.DoesNotExist:
                messages.error(request, "E-Mail/login does not exist.")
                return redirect('frontend:password_restore')

            password = User.objects.make_random_password()
            user.set_password(password)
            user.save()

            task = tasks.SendRestoredPassword(user.id, password)
            TaskManager.add(task)

            # check for multiple accounts from deprecated Orthos
            task = tasks.CheckMultipleAccounts(user.id)
            TaskManager.add(task)

            messages.success(request, "Password restored - check your mails.")
            return redirect('frontend:login')

    return render(
        request,
        'registration/password_reset.html', {
            'form': form,
            'title': 'Reset Password'
        }
    )


@login_required
def users_preferences(request):
    if request.method == 'GET':
        form = PreferencesForm()
    else:
        form = PreferencesForm(request.POST)

        if form.is_valid():
            try:
                user = User.objects.get(pk=request.user.id)
            except User.DoesNotExist:
                messages.error(request, "User does not exist.")
                return redirect('frontend:password_restore')

            new_password = form.cleaned_data['new_password']
            old_password = form.cleaned_data['old_password']

            if not user.check_password(old_password):
                messages.error(request, "Current password is wrong.")
                return redirect('frontend:preferences_user')

            user.set_password(new_password)
            user.save()

            user = authenticate(username=request.user.username, password=new_password)

            if user is not None:
                update_session_auth_hash(request, user)
                messages.success(request, "Password successfully changed.")
                return redirect('frontend:preferences_user')
            else:
                messages.error(request, "Something went wrong.")
                return redirect('frontend:login')

    return render(
        request,
        'registration/preferences.html', {
            'form': form,
            'title': 'Preferences'
        }
    )


@login_required
def machine_search(request):
    if request.method == 'GET':
        form = SearchForm()

    else:
        form = SearchForm(request.POST)

        if form.is_valid():
            machines = Machine.search.form(form.cleaned_data, request.user)
            return render(
                request,
                'machines/list.html', {
                    'machines': machines,
                    'title': 'Search Result'
                }
            )

    return render(
        request,
        'machines/search.html', {
            'form': form,
            'title': 'Advanced Search'
        }
    )


@login_required
def statistics(request):
    total = Machine.objects.all().count()

    status_ping = Machine.objects.filter(
        Q(status_ipv4=Machine.StatusIP.REACHABLE) |
        Q(status_ipv4=Machine.StatusIP.CONFIRMED) |
        Q(status_ipv6=Machine.StatusIP.REACHABLE) |
        Q(status_ipv6=Machine.StatusIP.CONFIRMED)
    ).count()
    status_ssh = Machine.objects.filter(status_ssh=True).count()
    status_login = Machine.objects.filter(status_login=True).count()
    status_abuild = Machine.objects.filter(status_abuild=True).count()

    check_ping = Machine.objects.filter(
        check_connectivity__gte=Machine.Connectivity.PING
    ).count()

    check_ssh = Machine.objects.filter(
        check_connectivity__gte=Machine.Connectivity.SSH
    ).count()

    check_login = Machine.objects.filter(
        check_connectivity__gte=Machine.Connectivity.ALL
    ).count()

    check_abuild = Machine.objects.filter(check_abuild=True).count()

    released_reservations = ReservationHistory.objects.filter(
        reserved_until__gt=timezone.make_aware(
            datetime.datetime.today() - datetime.timedelta(days=2),
            timezone.get_default_timezone()
        ),
        reserved_until__lte=timezone.make_aware(
            datetime.datetime.today(),
            timezone.get_default_timezone()
        )
    )

    reserved_machines = Machine.objects.filter(
        reserved_at__gt=timezone.make_aware(
            datetime.datetime.today() - datetime.timedelta(days=2),
            timezone.get_default_timezone()
        ),
        reserved_at__lte=timezone.make_aware(
            datetime.datetime.today(),
            timezone.get_default_timezone()
        )
    )

    matrix = [[], [], [], []]

    for architecture in Architecture.objects.all():
        matrix[0].append(architecture.machine_set.count())
        matrix[1].append(architecture.machine_set.filter(reserved_by=None).count())
        matrix[2].append(architecture.machine_set.filter(status_login=True).count())
        infinite = timezone.datetime.combine(datetime.date.max, timezone.datetime.min.time())
        infinite = timezone.make_aware(infinite, timezone.utc)
        matrix[3].append(architecture.machine_set.filter(reserved_until=infinite).count())

    matrix[0].append(sum(matrix[0]))
    matrix[1].append(sum(matrix[1]))
    matrix[2].append(sum(matrix[2]))
    matrix[3].append(sum(matrix[3]))

    data = {
        'total': total,
        'matrix': matrix,
        'status': {
            'labels': ['Ping', 'SSH', 'Login', 'ABuild'],
            'values1': [check_ping, check_ssh, check_login, check_abuild],
            'values2': [status_ping, status_ssh, status_login, status_abuild],
            'max': total if total % 100 == 0 else total - (total % 100) + 100
        },
        'domains': {
            'labels': list(Domain.objects.all().values_list('name', flat=True)),
            'values': [domain.machine_set.count() for domain in Domain.objects.all()]
        },
        'released_reservations': released_reservations,
        'reserved_machines': reserved_machines
    }

    return render(
        request,
        'machines/statistics.html', {
            'architectures': Architecture.objects.all(),
            'data': data,
            'title': 'Statistics'
        }
    )


def deprecate_current_app(func):
    """Handle deprecation of the current_app parameter of the views."""
    @functools.wraps(func)
    def inner(*args, **kwargs):
        if 'current_app' in kwargs:
            warnings.warn(
                "Passing `current_app` as a keyword argument is deprecated. "
                "Instead the caller of `{0}` should set "
                "`request.current_app`.".format(func.__name__)
            )
            current_app = kwargs.pop('current_app')
            request = kwargs.get('request', None)
            if request and current_app is not None:
                request.current_app = current_app
        return func(*args, **kwargs)
    return inner


def _get_login_redirect_url(request, redirect_to):
    # Ensure the user-originating redirection URL is safe.
    if not is_safe_url(url=redirect_to, host=request.get_host()):
        return resolve_url(settings.LOGIN_REDIRECT_URL)
    return redirect_to


@deprecate_current_app
@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, template_name='registration/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          extra_context=None, redirect_authenticated_user=False):
    """Display the login form and handles the login action."""
    redirect_to = request.POST.get(redirect_field_name, request.GET.get(redirect_field_name, ''))

    if redirect_authenticated_user and request.user.is_authenticated:
        redirect_to = _get_login_redirect_url(request, redirect_to)
        if redirect_to == request.path:
            raise ValueError(
                "Redirection loop for authenticated user detected. Check that "
                "your LOGIN_REDIRECT_URL doesn't point to a login page."
            )
        return HttpResponseRedirect(redirect_to)
    elif request.method == "POST":
        form = authentication_form(request, data=request.POST)

        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect('frontend:machines')
        else:
            # active users without password
            try:
                user = User.objects.get(username=request.POST['username'])
                if user.is_active and not user.password:
                    messages.info(request, "Please receive your inital password.")
                    url = reverse('frontend:password_restore')
                    return redirect('{}?user_id={}'.format(url, user.pk))
            except Exception:
                pass

            messages.error(request, "Unknown login/password!")

            form = authentication_form(request)
    else:
        form = authentication_form(request)

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
        'account_creation': ServerConfig.objects.bool_by_key(
            'auth.account.creation'),
        'title': 'Login'
    }
    if extra_context is not None:
        context.update(extra_context)

    welcome_message = ServerConfig.objects.by_key('orthos.web.welcomemessage')

    if welcome_message:
        messages.info(request, mark_safe(welcome_message))

    return TemplateResponse(request, template_name, context)
