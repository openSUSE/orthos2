import logging
import re

from orthos2.api.lookups import NotEqual
from orthos2.data.models import (Annotation, Architecture, Domain, Enclosure,
                                 Installation, Machine, MachineGroup, NetworkInterface,
                                 PCIDevice, Platform, RemotePower, SerialConsole,
                                 SerialConsoleType, System, User, Vendor)
from django.core.exceptions import (FieldDoesNotExist, FieldError,
                                    MultipleObjectsReturned)
from django.db.models import Field, Q
from django.db.models.functions import Length

logger = logging.getLogger('api')

Field.register_lookup(NotEqual)


class HelperFunctions:

    @staticmethod
    def get_ipv4(machine_id):
        """
        Return the IPv4 address of a machine.

        This value gets set after initialising a machine.
        """
        machine = Machine.objects.get(pk=machine_id)
        value = getattr(machine, 'ipv4', None)
        return value

    @staticmethod
    def get_ipv6(machine_id):
        """
        Return the IPv6 address of a machine.

        This value gets set after initialising a machine.
        """
        machine = Machine.objects.get(pk=machine_id)
        value = getattr(machine, 'ipv6', None)
        return value

    @staticmethod
    def username_to_id(username):
        """Translate a string into a valid user ID if possible."""
        try:
            return User.objects.get(username__iexact=username).pk
        except MultipleObjectsReturned:
            raise MultipleObjectsReturned("Found more than one user!")

    @staticmethod
    def get_status_ping(machine_id):
        """Return the ping status of a machine."""
        machine = Machine.objects.get(pk=machine_id)
        value = getattr(machine, 'status_ping', None)
        return value


class QueryField:

    LENGTH_SUFFIX = '_length'

    # non-database fields
    DYNAMIC_FIELDS = {
        'ipv4': {
            'verbose_name': 'IPv4',
            'function': HelperFunctions.get_ipv4
        },
        'ipv6': {
            'verbose_name': 'IPv6',
            'function': HelperFunctions.get_ipv6
        },
        'status_ping': {
            'verbose_name': 'Ping',
            'function': HelperFunctions.get_status_ping
        }
    }

    MAPPING = {
        # Aliases
        'architecture': {
            'field': Architecture._meta.get_field('name'),
            'related_name': 'architecture',
            'verbose_name': 'Architecture'
        },
        'name': {
            'field': Machine._meta.get_field('fqdn')
        },
        'domain': {
            'field': Domain._meta.get_field('name'),
            'related_name': 'fqdn_domain',
            'verbose_name': 'Domain'
        },
        'enclosure': {
            'field': Machine._meta.get_field('enclosure'),
            'pre': lambda x:
                Enclosure.objects.get(name__iexact=x) if isinstance(x, str) else x,
            'post': lambda x:
                Enclosure.objects.get(pk=x).name
        },
        'group': {
            'field': Machine._meta.get_field('group'),
            'pre': lambda x:
                MachineGroup.objects.get(name__iexact=x) if isinstance(x, str) else x,
            'post': lambda x:
                MachineGroup.objects.get(pk=x).name
        },
        'system': {
            'field': System._meta.get_field('name'),
            'related_name': 'system',
            'verbose_name': 'System',
            'pre': lambda x:
                x,
            'post': lambda x:
                x
        },
        'ram': {
            'field': Machine._meta.get_field('ram_amount')
        },
        'reserved_by': {
            'field': Machine._meta.get_field('reserved_by'),
            'pre': lambda x:
                HelperFunctions.username_to_id(x) if isinstance(x, str) else x,
            'post': lambda x:
                User.objects.get(pk=x).username
        },
        'res_by': {
            'field': Machine._meta.get_field('reserved_by'),
            'pre': lambda x:
                HelperFunctions.username_to_id(x) if isinstance(x, str) else x,
            'post': lambda x:
                User.objects.get(pk=x).username
        },
        'reserved_by_email': {
            'field': User._meta.get_field('email'),
            'related_name': 'reserved_by',
            'verbose_name': 'Email'
        },
        'status_ipv4': {
            'field': Machine._meta.get_field('status_ipv4'),
            'pre': lambda x:
                dict({
                    value: key for key, value in dict(Machine.StatusIP.CHOICE).items()
                }).get(x) if isinstance(x, str) else x,
            'post': lambda x:
                dict(Machine.StatusIP.CHOICE).get(x)
        },
        'status_ipv6': {
            'field': Machine._meta.get_field('status_ipv6'),
            'pre': lambda x:
                dict({
                    value: key for key, value in dict(Machine.StatusIP.CHOICE).items()
                }).get(x) if isinstance(x, str) else x,
            'post': lambda x:
                dict(Machine.StatusIP.CHOICE).get(x)
        },

        # SerialConsole
        'serial_console_server': {
            'field': SerialConsole._meta.get_field('console_server'),
            'related_name': 'serialconsole',
            'verbose_name': 'Console server',
            'pre': lambda x:
                Machine.objects.get(fqdn__iexact=x) if isinstance(x, str) else x,
            'post': lambda x:
                Machine.objects.get(pk=x).fqdn
        },
        'serial_cscreen_server': {
            'field': SerialConsole._meta.get_field('cscreen_server'),
            'related_name': 'serialconsole',
            'verbose_name': 'CScreen server',
            'pre': lambda x:
                Machine.objects.get(fqdn__iexact=x) if isinstance(x, str) else x,
            'post': lambda x:
                Machine.objects.get(pk=x).fqdn
        },
        'serial_management_bmc': {
            'field': SerialConsole._meta.get_field('management_bmc'),
            'related_name': 'serialconsole',
            'verbose_name': 'Management BMC',
            'pre': lambda x:
                Machine.objects.get(fqdn__iexact=x) if isinstance(x, str) else x,
            'post': lambda x:
                Machine.objects.get(pk=x).fqdn
        },
        'serial_type': {
            'field': SerialConsole._meta.get_field('type'),
            'related_name': 'serialconsole',
            'verbose_name': 'Serial console',
            'pre': lambda x:
                SerialConsoleType.Type.to_int(x) if isinstance(x, str) else x,
            'post': lambda x:
                SerialConsoleType.Type.to_str(x)
        },
        'sconsole': {
            'field': SerialConsole._meta.get_field('type'),
            'related_name': 'serialconsole',
            'verbose_name': 'Serial console',
            'pre': lambda x:
                SerialConsoleType.Type.to_int(x) if isinstance(x, str) else x,
            'post': lambda x:
                SerialConsoleType.Type.to_str(x)
        },
        'serial_baud': {
            'field': SerialConsole._meta.get_field('baud_rate'),
            'related_name': 'serialconsole',
            'verbose_name': 'Baud rate',
        },
        'serial_command': {
            'field': SerialConsole._meta.get_field('command'),
            'related_name': 'serialconsole',
            'verbose_name': 'Command',
        },
        'serial_device': {
            'field': SerialConsole._meta.get_field('device'),
            'related_name': 'serialconsole',
            'verbose_name': 'Device',
        },
        'serial_kernel_device': {
            'field': SerialConsole._meta.get_field('kernel_device'),
            'related_name': 'serialconsole',
            'verbose_name': 'Device',
        },
        'serial_port': {
            'field': SerialConsole._meta.get_field('port'),
            'related_name': 'serialconsole',
            'verbose_name': 'Port',
        },
        'serial_comment': {
            'field': SerialConsole._meta.get_field('comment'),
            'related_name': 'serialconsole',
            'verbose_name': 'Comment',
        },

        # RemotePower
        'rpower_management_bmc': {
            'field': RemotePower._meta.get_field('management_bmc'),
            'related_name': 'remotepower',
            'verbose_name': 'Management BMC',
            'pre': lambda x:
                Machine.objects.get(fqdn__iexact=x) if isinstance(x, str) else x,
            'post': lambda x:
                Machine.objects.get(pk=x).fqdn
        },
        'rpower_power_device': {
            'field': RemotePower._meta.get_field('remote_power_device'),
            'related_name': 'remotepower',
            'verbose_name': 'Remote power device',
            'pre': lambda x:
                Machine.objects.get(fqdn__iexact=x) if isinstance(x, str) else x,
            'post': lambda x:
                Machine.objects.get(pk=x).fqdn
        },
        'rpower_device': {
            'field': RemotePower._meta.get_field('device'),
            'related_name': 'remotepower',
            'verbose_name': 'Device',
        },
        'rpower_port': {
            'field': RemotePower._meta.get_field('port'),
            'related_name': 'remotepower',
            'verbose_name': 'Port',
        },
# TODO: adapt this to new implementation
#        'rpower_type': { 
#            'field': RemotePower._meta.get_field('type'),
#            'related_name': 'remotepower',
#            'verbose_name': 'Remotepower',
#            'pre': lambda x:
#                RemotePower.Type.to_int(x) if isinstance(x, str) else x,
#            'post': lambda x:
#                RemotePower.Type.to_str(x)
#        },
#        'rpower': {
#            'field': RemotePower._meta.get_field('type'),
#            'related_name': 'remotepower',
#            'verbose_name': 'Remotepower',
#            'pre': lambda x:
#                RemotePower.Type.to_int(x) if isinstance(x, str) else x,
#            'post': lambda x:
#                RemotePower.Type.to_str(x)
#        },

        # Installation
        'inst_active': {
            'field': Installation._meta.get_field('active'),
            'related_name': 'installations',
            'verbose_name': 'Active inst.'
        },
        'inst_arch': {
            'field': Installation._meta.get_field('architecture'),
            'related_name': 'installations',
            'verbose_name': 'Inst. architecture'
        },
        'inst_dist': {
            'field': Installation._meta.get_field('distribution'),
            'related_name': 'installations',
            'verbose_name': 'Distribution'
        },
        'inst_kernel': {
            'field': Installation._meta.get_field('kernelversion'),
            'related_name': 'installations',
            'verbose_name': 'Kernel version'
        },
        'inst_partition': {
            'field': Installation._meta.get_field('partition'),
            'related_name': 'installations',
            'verbose_name': 'Partition'
        },

        # NetworkInterface
        'iface_driver_module': {
            'field': NetworkInterface._meta.get_field('driver_module'),
            'related_name': 'networkinterfaces',
            'verbose_name': 'IF driver module'
        },
        'iface_ethernet_type': {
            'field': NetworkInterface._meta.get_field('ethernet_type'),
            'related_name': 'networkinterfaces',
            'verbose_name': 'IF ethernet type'
        },
        'iface_mac_address': {
            'field': NetworkInterface._meta.get_field('mac_address'),
            'related_name': 'networkinterfaces',
            'verbose_name': 'IF MAC address'
        },
        'iface_name': {
            'field': NetworkInterface._meta.get_field('name'),
            'related_name': 'networkinterfaces',
            'verbose_name': 'IF name'
        },
        'iface_primary': {
            'field': NetworkInterface._meta.get_field('primary'),
            'related_name': 'networkinterfaces',
            'verbose_name': 'IF primary'
        },

        # PCIDevice
        'pci_slot': {
            'field': PCIDevice._meta.get_field('slot'),
            'related_name': 'pcidevice',
            'verbose_name': 'Slot'
        },
        'pci_vendorid': {
            'field': PCIDevice._meta.get_field('vendor_id'),
            'related_name': 'pcidevice',
            'verbose_name': 'Vendor ID'
        },
        'pci_vendor': {
            'field': PCIDevice._meta.get_field('vendor'),
            'related_name': 'pcidevice',
            'verbose_name': 'Vendor'
        },
        'pci_deviceid': {
            'field': PCIDevice._meta.get_field('device_id'),
            'related_name': 'pcidevice',
            'verbose_name': 'Device ID'
        },
        'pci_device': {
            'field': PCIDevice._meta.get_field('device'),
            'related_name': 'pcidevice',
            'verbose_name': 'Device'
        },
        'pci_classid': {
            'field': PCIDevice._meta.get_field('class_id'),
            'related_name': 'pcidevice',
            'verbose_name': 'Class ID'
        },
        'pci_classname': {
            'field': PCIDevice._meta.get_field('classname'),
            'related_name': 'pcidevice',
            'verbose_name': 'Class name'
        },
        'pci_svendorid': {
            'field': PCIDevice._meta.get_field('subvendor_id'),
            'related_name': 'pcidevice',
            'verbose_name': 'Subvendor ID'
        },
        'pci_svendorname': {
            'field': PCIDevice._meta.get_field('subvendor'),
            'related_name': 'pcidevice',
            'verbose_name': 'Subvendor'
        },
        'pci_sdeviceid': {
            'field': PCIDevice._meta.get_field('subdevice_id'),
            'related_name': 'pcidevice',
            'verbose_name': 'Subdevice ID'
        },
        'pci_sdevicename': {
            'field': PCIDevice._meta.get_field('subdevice'),
            'related_name': 'pcidevice',
            'verbose_name': 'Subdevice'
        },
        'pci_revision': {
            'field': PCIDevice._meta.get_field('revision'),
            'related_name': 'pcidevice',
            'verbose_name': 'Revision'
        },
        'pci_driver': {
            'field': PCIDevice._meta.get_field('drivermodule'),
            'related_name': 'pcidevice',
            'verbose_name': 'Drivermodule'
        },

        # Platform
        'enclosure_platform': {
            'field': Platform._meta.get_field('name'),
            'related_name': 'enclosure__platform',
            'verbose_name': 'Platform'
        },

        # Vendor
        'enclosure_vendor': {
            'field': Vendor._meta.get_field('name'),
            'related_name': 'enclosure__platform__vendor',
            'verbose_name': 'Vendor'
        },

        # Annotation
        'annotation_text': {
            'field': Annotation._meta.get_field('text'),
            'related_name': 'annotations',
            'verbose_name': 'Annotation'
        },
        'annotation_reporter': {
            'field': Annotation._meta.get_field('reporter'),
            'related_name': 'annotations',
            'verbose_name': 'Reporter',
            'pre': lambda x:
                HelperFunctions.username_to_id(x) if isinstance(x, str) else x,
            'post': lambda x:
                User.objects.get(pk=x).username
        },
        'annotation_created': {
            'field': Annotation._meta.get_field('created'),
            'related_name': 'annotations',
            'verbose_name': 'Created',
        }
    }

    def __init__(self, token):
        """
        Constructor for `QueryField`.

        This constructor tries to define a valid query field with
        all corresponding values for further processing in the context of DB querying.

        Example:
            QueryField('comment')                -> Machine.comment
            QueryField('comment_length')         -> Machine.comment (for querying the char length)
            QueryField('ipv4')                   -> Machine.ipv4 (dynamic field)
            QueryField('installations__comment') -> Machine.installations.comment (related field)
        """
        self._field = None
        self._related_name = None
        self._verbose_name = None
        self._dynamic = False
        self._pre_function = None
        self._post_function = None

        if self.LENGTH_SUFFIX in token:
            token = token.replace(self.LENGTH_SUFFIX, '')
            self._annotation = self.LENGTH_SUFFIX
        else:
            self._annotation = None

        try:
            self._field = self.MAPPING[token]['field']
            self._verbose_name = self.MAPPING[token].get('verbose_name')
            if not self._verbose_name:
                self._verbose_name = Machine._meta.get_field(self._field.name).verbose_name
            self._related_name = self.MAPPING[token].get('related_name')
            self._pre_function = self.MAPPING[token].get('pre')
            self._post_function = self.MAPPING[token].get('post')
        except KeyError:
            pass

        if not self._field and (token in self.DYNAMIC_FIELDS):
            self._field = Field(name=token)
            self._verbose_name = self.DYNAMIC_FIELDS[self._field.name]['verbose_name']
            self._dynamic_field_function = self.DYNAMIC_FIELDS[self._field.name]['function']
            self._dynamic = True

        if not self._field:
            try:
                self._field = Machine._meta.get_field(token)
                self._verbose_name = self._field.verbose_name
            except FieldDoesNotExist:
                pass

        if not self._field:
            related_name = '__'.join(token.split('__')[:-1])
            field_name = token.split('__')[-1]

            if related_name:
                for token, values in self.MAPPING.items():
                    if related_name == values.get('related_name'):
                        if field_name == values['field'].name:
                            self._field = self.MAPPING[token]['field']
                            self._related_name = related_name
                            self._verbose_name = self.MAPPING[token]['verbose_name']
                            self._pre_function = self.MAPPING[token].get('pre')
                            self._post_function = self.MAPPING[token].get('post')

        if not self._field:
            raise ValueError("Unknown field '{}'!".format(token))

    def __str__(self):
        return self.db_field_name

    def __repr__(self):
        if not self.is_dynamic:
            return '<{}: {}>'.format(self.__class__.__name__, self.db_field_name)
        return '<{}: {} (dynamic)>'.format(self.__class__.__name__, self.db_field_name)

    @classmethod
    def get_valid_field_names(cls):
        """
        Return a list of valid field names.

        These are all `Machine` field names, all `MAPPING` field names and all dynamic field names
        in `DYNAMIC_FIELDS`.
        """
        field_names = [field.name for field in Machine._meta.fields]
        field_names += list(cls.MAPPING.keys())
        field_names += list(cls.DYNAMIC_FIELDS.keys())
        return field_names

    @property
    def db_field_name(self):
        """Return a valid field name for querying the DB."""
        if self._related_name:
            field_name = '{}__{}'.format(self._related_name, self._field.name)
        else:
            field_name = self._field.name

        if self._annotation is not None:
            field_name += self._annotation

        return field_name

    @property
    def related_name(self):
        """Return the related name of a `QueryField` object."""
        return self._related_name

    @property
    def verbose_name(self):
        """Return the verbose name of a `QueryField` object."""
        if self._verbose_name.islower():
            return self._verbose_name.capitalize()
        return self._verbose_name

    @property
    def null(self):
        """Return if a `QueryField` object can be `NULL` in the DB."""
        return self._field.null

    @property
    def is_dynamic(self):
        """Return if a `QueryField` object is dynamic (non-database value) or not."""
        return self._dynamic

    def is_BooleanField(self):
        """Check if a `QueryField` object is a boolean field."""
        return 'BooleanField' in self._field.get_internal_type()

    def is_CharField(self):
        """Check if a `QueryField` object is a character field."""
        return 'CharField' in self._field.get_internal_type()

    def is_TextField(self):
        """Check if a `QueryField` object is a character field."""
        return 'TextField' in self._field.get_internal_type()

    def is_ForeignKey(self):
        """Check if a `QueryField` object is a foreign key."""
        return 'ForeignKey' in self._field.get_internal_type()

    def is_DateField(self):
        """Check if a `QueryField` object is a date field."""
        return 'DateField' in self._field.get_internal_type()

    def is_DateTimeField(self):
        """Check if a `QueryField` object is a datetime field."""
        return 'DateTimeField' in self._field.get_internal_type()

    def get_db_function_length(self):
        """
        Return a tuple with a valid DB field name for querying string length and its corresponding
        DB function.

        Example:
            ('comment_length', Length('comment'))
        """
        field = QueryField(self.db_field_name + self.LENGTH_SUFFIX)
        return (field, {field.db_field_name: Length(self.db_field_name)})

    @property
    def type(self):
        """Return fields type as string."""
        return self._field.get_internal_type()

    @property
    def dynamic_field_function(self):
        """
        Return a optional function for processing dynamic fields (non-database fields).

        If no dynamic function is defined, a simple lambda function is returned which simply
        returns the input value.
        """
        if self._dynamic_field_function:
            return self._dynamic_field_function
        return lambda x: x

    @property
    def pre_function(self):
        """
        Return a optional pre-function.

        If no pre-function is defined, a simple lambda function is returned which simply returns
        the input value.
        """
        if self._pre_function:
            return self._pre_function
        return lambda x: x

    @property
    def post_function(self):
        """
        Return a optional post-function.

        If no post-function is defined, a simple lambda function is returned which simply returns
        the input value.
        """
        if self._post_function:
            return self._post_function
        return lambda x: x


class APIQuery:

    class EmptyResult(Exception):
        pass

    OPERATORS = {
        '=': {
            '__default__': '__iexact',
            'DateTimeField': '',
            'ForeignKey': '',
        },
        '==': {
            '__default__': '__iexact',
            'DateTimeField': '',
            'ForeignKey': '',
        },
        '=~': {
            '__default__': '__icontains',
        },
        '=*': {
            '__default__': '__istartswith',
        },
        '!=': {
            '__default__': '__ne',
        },
        '>': {
            '__default__': '__gt',
        },
        '>=': {
            '__default__': '__gte',
        },
        '<': {
            '__default__': '__lt',
        },
        '<=': {
            '__default__': '__lte',
        }
    }

    AND = 'and'
    OR = 'or'
    WHERE = 'where'

    def __init__(self, query_str):
        self._query_str = query_str.strip()
        self._query = None
        self._data = None
        self._fields = []
        self._conditions = []
        self._conjunctions = []
        self._annotations = []

    def _prepare_query(self):
        """
        Split raw query string into field and condition section (if available) and preprocesses the
        data.

        Example:
            "<fields> where <condition> <conjunction> <condition> ..." ->
                [<fields>],
                [<conditions>],
                [<conjunctions>],
                [<annotations>]
        """
        query = re.split(self.WHERE, self._query_str)

        self._fields = self._prepare_fields(query[0])

        if len(query) == 2:
            if not query[1]:
                raise SyntaxError("Invalid syntax (expect at least one condition)!")

            self._conditions = self._prepare_conditions(query[1])[0]
            self._conjunctions = self._prepare_conditions(query[1])[1]
            self._annotations = self._prepare_conditions(query[1])[2]

        elif len(query) > 2:
            raise SyntaxError("Invalid syntax (multiple 'where' found)!")

    def _prepare_fields(self, fields_str):
        """Strip query string in query fields."""
        fields = []

        for token in fields_str.split(','):
            field = QueryField(token.strip())
            fields.append(field.db_field_name)

        return fields

    def _prepare_conditions(self, conditions_str):
        """
        Assemble conditions.

        For single condition statements on character fields, annotations get added for string
        length comparing.

        Return:
            (
                ['(<field>', '__<op>', '<value>'), ...],
                ['and', 'or', ...],
                ['<field>_lenght', Length(<field>), ...]
            )

        Examples:
            where foo ...           -> [('foo', '', 'True'), ...]
            where !foo ...          -> [('foo', '', 'False'), ...]
            where foo =~ bar ...    -> [('foo', '__istartswith', 'bar'), ...]
            where comment ...       -> [('comment_length', '__gt', 0, ...]
        """
        conditions = []
        conjunctions = []
        annotations = []
        condition = ()
        state = -1

        tokens = []
        for token in re.split(''' (?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', conditions_str.strip()):
            tokens.append(token.strip('"').strip("'"))

        for i, token in enumerate(tokens):
            token = token.strip()

            if i + 1 < len(tokens):
                next_token = tokens[i + 1].strip()
            else:
                next_token = None

            if state == -1 and (next_token and next_token in self.OPERATORS.keys()):
                # where <field> = value ...

                field = QueryField(token)

                condition = (field,)
                state = 0

            elif state == -1 and\
                    (not next_token or (next_token in {self.AND, self.OR}))\
                    and token not in {self.AND, self.OR}:
                # single field without condition
                # where <field> and ...
                if token[0] == '!':
                    token = token[1:]
                    is_not = True
                else:
                    is_not = False

                field = QueryField(token)

                if field.null:
                    filter = '__isnull'
                    value = is_not

                elif field.is_BooleanField():
                    filter = ''
                    value = not is_not

                elif field.is_CharField() or field.is_TextField():
                    field, annotation = field.get_db_function_length()
                    annotations.append(annotation)
                    if is_not:
                        filter = ''
                        value = 0
                    else:
                        filter = '__gt'
                        value = 0

                else:
                    filter = '__isnull'
                    value = is_not

                condition = (field, filter, value)
                conditions.append(condition)

            elif state == 0:
                # where field <operator> value ...

                field = condition[0]

                try:
                    operator = self.OPERATORS[token][field.type]
                except KeyError:
                    operator = self.OPERATORS[token]['__default__']

                condition = condition + (operator,)
                state = 1

            elif state == 1:
                # where field = <value> ...
                # replace '%20' with whitespace; Example:
                #   query ... where inst_dist =* 'sles 12' -> 'sles%2012' -> 'sles 12'
                token = token.replace('%20', ' ')

                if condition[0].is_DateTimeField() and token.lower() == 'infinite':
                    if condition[1] == '__iexact':
                        # no timezone offset here
                        token = '9999-12-31 00:00:00'
                    else:
                        token = '9999-12-31 00:00+0000'

                condition = condition + (token,)
                state = -1

                if condition[0].type == 'ForeignKey' and condition[1] == '__ne':
                    # for foreign keys use '<' (__lt) and '>' (__gt) for '!='
                    conditions.append((condition[0], '__gt', condition[2]))
                    conjunctions.append(self.OR)
                    conditions.append((condition[0], '__lt', condition[2]))
                else:
                    conditions.append(condition)

            elif next_token and token == self.AND:
                conjunctions.append(self.AND)

            elif next_token and token == self.OR:
                conjunctions.append(self.OR)

            else:
                raise Exception("Invalid condition!")

        return (conditions, conjunctions, annotations)

    def _get_query(self):
        """Return valid django model queries which can be piped into `filter()` method."""
        if self.has_conditions:
            if not self._conditions:
                raise Exception("Missing condition!")

            field, op, value = self._conditions[0]

            if field.is_dynamic:
                raise NotImplementedError("Non-database (dynamic) fields are not supported!")

            query = Q(**{'{}{}'.format(field.db_field_name, op): value})

            for i in range(0, len(self._conditions) - 1):
                field, op, value = self._conditions[i + 1]

                if field.is_dynamic:
                    raise NotImplementedError("Non-database (dynamic) fields are not supported!")

                try:
                    left = query
                    right = Q(**{'{}{}'.format(field.db_field_name, op): value})
                except IndexError:
                    raise Exception("Invalid query!")

                if i < len(self._conjunctions):
                    if self._conjunctions[i] == self.AND:
                        query = left & right
                    elif self._conjunctions[i] == self.OR:
                        query = left | right

            return query
        else:
            return Q()

    def execute(self, user=None):
        """
        Execute requested query and stores the result.

        This method is responsible for preparing, executing and revising data from the DB.
        """
        self._prepare_query()
        self._apply_pre_functions()

        query = self._get_query()

        logger.debug("Execute query: {}".format(query))

        # set `user` in order to prevent search results including administrative systems
        queryset = Machine.search.get_queryset(user=user)

        for annotation in self._annotations:
            queryset = queryset.annotate(**annotation)

        queryset = queryset.filter(query).distinct()

        if queryset:
            result = list(
                queryset.values(
                    *list(set(self._fields) - set(QueryField.DYNAMIC_FIELDS)) + ['pk']
                )
            )
        else:
            raise self.EmptyResult("No results found!")

        if not result:
            raise self.EmptyResult("No results found!")

        self._data = result
        self._data = self._add_dynamic_fields(self._data)
        self._data = self._apply_post_functions(self._data)

    def _add_dynamic_fields(self, rows):
        """
        Fields which are non-database fields needs to be queried and added separately using
        the primary key. If the primary key wasn't requested, remove it.
        """
        for machine in rows:
            for dynamic_field, values in QueryField.DYNAMIC_FIELDS.items():
                field = QueryField(dynamic_field)
                if field.db_field_name in self._fields:
                    machine[field.db_field_name] = field.dynamic_field_function(machine['pk'])

        # removal needs to be done here due to multiple pk lookups above
        for machine in rows:
            if 'pk' not in self._fields:
                machine.pop('pk', None)

        return rows

    def _apply_pre_functions(self):
        """
        Apply pre-functions.

        Pre-functions are used for converting user input values. This can be used for e.g.
        translating a search string into a foreign key integer.
        """
        for i, condition in enumerate(self._conditions):
            field = condition[0]

            try:
                value = int(condition[2])
            except ValueError:
                value = condition[2]

            self._conditions[i] = (
                condition[0],
                condition[1],
                field.pre_function(value)
            )

    def _apply_post_functions(self, rows):
        """Apply post-functions on each result row."""
        for row in rows:
            for field, value in row.items():
                if value is None:
                    continue
                field = QueryField(field)
                row[field.db_field_name] = field.post_function(value)

        return rows

    @property
    def has_conditions(self):
        return bool(self._conditions)

    @property
    def data(self):
        return self._data

    def get_theader(self):
        """
        Return fields for table header with verbose name specified in the model or manually in
        class `QueryField`.
        """
        result = []

        for token in self._fields:
            field = QueryField(token)
            result.append({field.db_field_name: field.verbose_name})

        return result

    @staticmethod
    def get_tab_completion_options():
        """Return fields, operators, etc. for tab completion as list."""
        options = QueryField.get_valid_field_names()
        options += list(APIQuery.OPERATORS.keys())
        options += [APIQuery.WHERE, APIQuery.AND, APIQuery.OR, 'infinite']

        return options
