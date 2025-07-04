import logging
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser, User
from django.core.exceptions import FieldDoesNotExist, MultipleObjectsReturned
from django.db.models import Field, Q
from django.db.models.functions import Length

from orthos2.api.lookups import NotEqual
from orthos2.data.models import (
    Annotation,
    Architecture,
    Domain,
    Enclosure,
    Installation,
    Machine,
    MachineGroup,
    NetworkInterface,
    PCIDevice,
    Platform,
    RemotePower,
    SerialConsole,
    SerialConsoleType,
    System,
    Vendor,
)

logger = logging.getLogger("api")

Field.register_lookup(NotEqual)


class HelperFunctions:
    @staticmethod
    def get_ipv4(machine_id: int) -> Optional[str]:
        """
        Return the IPv4 address of a machine.

        This value gets set after initialising a machine.
        """
        machine = Machine.objects.get(pk=machine_id)
        value = getattr(machine, "ip_address_v4", None)
        return value

    @staticmethod
    def get_ipv6(machine_id: int) -> Optional[str]:
        """
        Return the IPv6 address of a machine.

        This value gets set after initialising a machine.
        """
        machine = Machine.objects.get(pk=machine_id)
        value = getattr(machine, "ip_address_v6", None)
        return value

    @staticmethod
    def username_to_id(username: str) -> int:
        """Translate a string into a valid user ID if possible."""
        try:
            return User.objects.get(username__iexact=username).pk
        except MultipleObjectsReturned:
            raise MultipleObjectsReturned("Found more than one user!")

    @staticmethod
    def get_status_ping(machine_id: int) -> Optional[bool]:
        """Return the ping status of a machine."""
        machine = Machine.objects.get(pk=machine_id)
        value = getattr(machine, "status_ping", None)
        return value


@dataclass
class QueryFieldMappingItem:
    """
    A dataclass to allow safe & typed access to the common datastructures that the mapping is made from.
    """

    field: Field  # type: ignore
    related_name: str = ""
    verbose_name: str = ""
    pre: Optional[Callable[[Any], Any]] = None
    post: Optional[Callable[[Any], Any]] = None


@dataclass
class QueryFieldDynamicMappingItem:
    """
    A dataclass to allow safe & typed access to the common datastructures that the mapping is made from.
    """

    verbose_name: str
    function: Callable[[int], Union[bool, str, None]]


class QueryField:

    LENGTH_SUFFIX = "_length"

    # non-database fields
    DYNAMIC_FIELDS: Dict[str, QueryFieldDynamicMappingItem] = {
        "ipv4": QueryFieldDynamicMappingItem(
            verbose_name="IPv4", function=HelperFunctions.get_ipv4
        ),
        "ipv6": QueryFieldDynamicMappingItem(
            verbose_name="IPv6", function=HelperFunctions.get_ipv6
        ),
        "status_ping": QueryFieldDynamicMappingItem(
            verbose_name="Ping", function=HelperFunctions.get_status_ping
        ),
    }

    MAPPING: Dict[str, QueryFieldMappingItem] = {
        # Aliases
        "architecture": QueryFieldMappingItem(
            field=Architecture._meta.get_field("name"),  # type: ignore
            related_name="architecture",
            verbose_name="Architecture",
        ),
        "name": QueryFieldMappingItem(
            field=Machine._meta.get_field("fqdn"),  # type: ignore
        ),
        "domain": QueryFieldMappingItem(
            field=Domain._meta.get_field("name"),  # type: ignore
            related_name="fqdn_domain",
            verbose_name="Domain",
        ),
        "enclosure": QueryFieldMappingItem(
            field=Machine._meta.get_field("enclosure"),  # type: ignore
            pre=lambda x: (
                Enclosure.objects.get(name__iexact=x) if isinstance(x, str) else x
            ),
            post=lambda x: Enclosure.objects.get(pk=x).name,
        ),
        "group": QueryFieldMappingItem(
            field=Machine._meta.get_field("group"),  # type: ignore
            pre=lambda x: (
                MachineGroup.objects.get(name__iexact=x) if isinstance(x, str) else x
            ),
            post=lambda x: MachineGroup.objects.get(pk=x).name,
        ),
        "system": QueryFieldMappingItem(
            field=System._meta.get_field("name"),  # type: ignore
            related_name="system",
            verbose_name="System",
            pre=lambda x: x,
            post=lambda x: x,
        ),
        "ram": QueryFieldMappingItem(
            field=Machine._meta.get_field("ram_amount"),  # type: ignore
        ),
        "cobbler_server": QueryFieldMappingItem(
            field=Domain._meta.get_field("cobbler_server"),  # type: ignore
            related_name="fqdn_domain",
            verbose_name="Cobbler server",
            pre=lambda x: (
                Machine.objects.get(fqdn__iexact=x) if isinstance(x, str) else x
            ),
            post=lambda x: Machine.objects.get(pk=x).fqdn,
        ),
        "reserved_by": QueryFieldMappingItem(
            field=Machine._meta.get_field("reserved_by"),  # type: ignore
            pre=lambda x: (
                HelperFunctions.username_to_id(x) if isinstance(x, str) else x
            ),
            post=lambda x: User.objects.get(pk=x).username,  # type: ignore
        ),
        "res_by": QueryFieldMappingItem(
            field=Machine._meta.get_field("reserved_by"),  # type: ignore
            pre=lambda x: (
                HelperFunctions.username_to_id(x) if isinstance(x, str) else x
            ),
            post=lambda x: User.objects.get(pk=x).username,  # type: ignore
        ),
        "reserved_by_email": QueryFieldMappingItem(
            field=User._meta.get_field("email"),  # type: ignore
            related_name="reserved_by",
            verbose_name="Email",
        ),
        "status_ipv4": QueryFieldMappingItem(
            field=Machine._meta.get_field("status_ipv4"),  # type: ignore
            pre=lambda x: (
                dict(
                    {value: key for key, value in dict(Machine.StatusIP.CHOICE).items()}
                ).get(x)
                if isinstance(x, str)
                else x
            ),
            post=lambda x: dict(Machine.StatusIP.CHOICE).get(x),
        ),
        "status_ipv6": QueryFieldMappingItem(
            field=Machine._meta.get_field("status_ipv6"),  # type: ignore
            pre=lambda x: (
                dict(
                    {value: key for key, value in dict(Machine.StatusIP.CHOICE).items()}
                ).get(x)
                if isinstance(x, str)
                else x
            ),
            post=lambda x: dict(Machine.StatusIP.CHOICE).get(x),
        ),
        # SerialConsole
        "serial_console_server": QueryFieldMappingItem(
            field=SerialConsole._meta.get_field("console_server"),  # type: ignore
            related_name="serialconsole",
            verbose_name="Console server",
            pre=lambda x: (
                Machine.objects.get(fqdn__iexact=x) if isinstance(x, str) else x
            ),
            post=lambda x: Machine.objects.get(pk=x).fqdn,
        ),
        "serial_type": QueryFieldMappingItem(
            field=SerialConsole._meta.get_field("stype"),  # type: ignore
            related_name="serialconsole",
            verbose_name="Serial console",
            pre=lambda x: SerialConsoleType.Type.to_int(x) if isinstance(x, str) else x,
            post=lambda x: SerialConsoleType.Type.to_str(x),
        ),
        "sconsole": QueryFieldMappingItem(
            field=SerialConsole._meta.get_field("stype"),  # type: ignore
            related_name="serialconsole",
            verbose_name="Serial console",
            pre=lambda x: SerialConsoleType.Type.to_int(x) if isinstance(x, str) else x,
            post=lambda x: SerialConsoleType.Type.to_str(x),
        ),
        "serial_baud": QueryFieldMappingItem(
            field=SerialConsole._meta.get_field("baud_rate"),  # type: ignore
            related_name="serialconsole",
            verbose_name="Baud rate",
        ),
        "serial_command": QueryFieldMappingItem(
            field=SerialConsole._meta.get_field("command"),  # type: ignore
            related_name="serialconsole",
            verbose_name="Command",
        ),
        "serial_kernel_device": QueryFieldMappingItem(
            field=SerialConsole._meta.get_field("kernel_device"),  # type: ignore
            related_name="serialconsole",
            verbose_name="Kernel Device",
        ),
        "serial_kernel_device_num": QueryFieldMappingItem(
            field=SerialConsole._meta.get_field("kernel_device_num"),  # type: ignore
            related_name="serialconsole",
            verbose_name="Kernel Device number",
        ),
        "serial_port": QueryFieldMappingItem(
            field=SerialConsole._meta.get_field("port"),  # type: ignore
            related_name="serialconsole",
            verbose_name="Port",
        ),
        "serial_comment": QueryFieldMappingItem(
            field=SerialConsole._meta.get_field("comment"),  # type: ignore
            related_name="serialconsole",
            verbose_name="Comment",
        ),
        "rpower_device": QueryFieldMappingItem(
            field=RemotePower._meta.get_field("remote_power_device"),  # type: ignore
            related_name="remotepower",
            verbose_name="Remote power device",
            pre=lambda x: (
                Machine.objects.get(fqdn__iexact=x) if isinstance(x, str) else x
            ),
            post=lambda x: Machine.objects.get(pk=x).fqdn,
        ),
        "rpower_port": QueryFieldMappingItem(
            field=RemotePower._meta.get_field("port"),  # type: ignore
            related_name="remotepower",
            verbose_name="Port",
        ),
        # TODO: adapt this to new implementation
        "rpower_type": QueryFieldMappingItem(
            field=RemotePower._meta.get_field("fence_agent"),  # type: ignore
            related_name="remotepower",
            verbose_name="Remotepower type",
        ),
        # Installation
        "inst_active": QueryFieldMappingItem(
            field=Installation._meta.get_field("active"),  # type: ignore
            related_name="installations",
            verbose_name="Active inst.",
        ),
        "inst_arch": QueryFieldMappingItem(
            field=Installation._meta.get_field("architecture"),  # type: ignore
            related_name="installations",
            verbose_name="Inst. architecture",
        ),
        "inst_dist": QueryFieldMappingItem(
            field=Installation._meta.get_field("distribution"),  # type: ignore
            related_name="installations",
            verbose_name="Distribution",
        ),
        "inst_kernel": QueryFieldMappingItem(
            field=Installation._meta.get_field("kernelversion"),  # type: ignore
            related_name="installations",
            verbose_name="Kernel version",
        ),
        "inst_partition": QueryFieldMappingItem(
            field=Installation._meta.get_field("partition"),  # type: ignore
            related_name="installations",
            verbose_name="Partition",
        ),
        # NetworkInterface
        "iface_driver_module": QueryFieldMappingItem(
            field=NetworkInterface._meta.get_field("driver_module"),  # type: ignore
            related_name="networkinterfaces",
            verbose_name="IF driver module",
        ),
        "iface_ethernet_type": QueryFieldMappingItem(
            field=NetworkInterface._meta.get_field("ethernet_type"),  # type: ignore
            related_name="networkinterfaces",
            verbose_name="IF ethernet type",
        ),
        "iface_mac_address": QueryFieldMappingItem(
            field=NetworkInterface._meta.get_field("mac_address"),  # type: ignore
            related_name="networkinterfaces",
            verbose_name="IF MAC address",
        ),
        "iface_name": QueryFieldMappingItem(
            field=NetworkInterface._meta.get_field("name"),  # type: ignore
            related_name="networkinterfaces",
            verbose_name="IF name",
        ),
        "iface_primary": QueryFieldMappingItem(
            field=NetworkInterface._meta.get_field("primary"),  # type: ignore
            related_name="networkinterfaces",
            verbose_name="IF primary",
        ),
        # PCIDevice
        "pci_slot": QueryFieldMappingItem(
            field=PCIDevice._meta.get_field("slot"),  # type: ignore
            related_name="pcidevice",
            verbose_name="Slot",
        ),
        "pci_vendorid": QueryFieldMappingItem(
            field=PCIDevice._meta.get_field("vendor_id"),  # type: ignore
            related_name="pcidevice",
            verbose_name="Vendor ID",
        ),
        "pci_vendor": QueryFieldMappingItem(
            field=PCIDevice._meta.get_field("vendor"),  # type: ignore
            related_name="pcidevice",
            verbose_name="Vendor",
        ),
        "pci_deviceid": QueryFieldMappingItem(
            field=PCIDevice._meta.get_field("device_id"),  # type: ignore
            related_name="pcidevice",
            verbose_name="Device ID",
        ),
        "pci_device": QueryFieldMappingItem(
            field=PCIDevice._meta.get_field("device"),  # type: ignore
            related_name="pcidevice",
            verbose_name="Device",
        ),
        "pci_classid": QueryFieldMappingItem(
            field=PCIDevice._meta.get_field("class_id"),  # type: ignore
            related_name="pcidevice",
            verbose_name="Class ID",
        ),
        "pci_classname": QueryFieldMappingItem(
            field=PCIDevice._meta.get_field("classname"),  # type: ignore
            related_name="pcidevice",
            verbose_name="Class name",
        ),
        "pci_svendorid": QueryFieldMappingItem(
            field=PCIDevice._meta.get_field("subvendor_id"),  # type: ignore
            related_name="pcidevice",
            verbose_name="Subvendor ID",
        ),
        "pci_svendorname": QueryFieldMappingItem(
            field=PCIDevice._meta.get_field("subvendor"),  # type: ignore
            related_name="pcidevice",
            verbose_name="Subvendor",
        ),
        "pci_sdeviceid": QueryFieldMappingItem(
            field=PCIDevice._meta.get_field("subdevice_id"),  # type: ignore
            related_name="pcidevice",
            verbose_name="Subdevice ID",
        ),
        "pci_sdevicename": QueryFieldMappingItem(
            field=PCIDevice._meta.get_field("subdevice"),  # type: ignore
            related_name="pcidevice",
            verbose_name="Subdevice",
        ),
        "pci_revision": QueryFieldMappingItem(
            field=PCIDevice._meta.get_field("revision"),  # type: ignore
            related_name="pcidevice",
            verbose_name="Revision",
        ),
        "pci_driver": QueryFieldMappingItem(
            field=PCIDevice._meta.get_field("drivermodule"),  # type: ignore
            related_name="pcidevice",
            verbose_name="Drivermodule",
        ),
        # Platform
        "platform": QueryFieldMappingItem(
            field=Platform._meta.get_field("name"),  # type: ignore
            related_name="platform",
            verbose_name="Platform",
        ),
        "platform_vendor": QueryFieldMappingItem(
            field=Vendor._meta.get_field("name"),  # type: ignore
            related_name="platform__vendor",
            verbose_name="Vendor",
        ),
        "platform_description": QueryFieldMappingItem(
            field=Platform._meta.get_field("description"),  # type: ignore
            related_name="platform",
            verbose_name="Platform description",
        ),
        # Annotation
        "annotation_text": QueryFieldMappingItem(
            field=Annotation._meta.get_field("text"),  # type: ignore
            related_name="annotations",
            verbose_name="Annotation",
        ),
        "annotation_reporter": QueryFieldMappingItem(
            field=Annotation._meta.get_field("reporter"),  # type: ignore
            related_name="annotations",
            verbose_name="Reporter",
            pre=lambda x: (
                HelperFunctions.username_to_id(x) if isinstance(x, str) else x
            ),
            post=lambda x: User.objects.get(pk=x).username,  # type: ignore
        ),
        "annotation_created": QueryFieldMappingItem(
            field=Annotation._meta.get_field("created"),  # type: ignore
            related_name="annotations",
            verbose_name="Created",
        ),
    }

    def __init__(self, token: str) -> None:
        """
        Constructor for `QueryField`.

        This constructor tries to define a valid query field with
        all corresponding values for further processing in the context of DB querying.

        Example:
            QueryField('comment')                -> Machine.comment
            QueryField('comment_length')         -> Machine.comment (for querying the char length)
            QueryField('mac_address')            -> Machine.mac_address (dynamic field)
            QueryField('installations__comment') -> Machine.installations.comment (related field)
        """
        field = None
        self._related_name = None
        self._verbose_name = None
        self._dynamic = False
        self._pre_function = None
        self._post_function = None

        if self.LENGTH_SUFFIX in token:
            token = token.replace(self.LENGTH_SUFFIX, "")
            self._annotation: Optional[str] = self.LENGTH_SUFFIX
        else:
            self._annotation = None

        try:
            field = self.MAPPING[token].field  # type: ignore
            self._verbose_name = self.MAPPING[token].verbose_name
            if not self._verbose_name:
                self._verbose_name = Machine._meta.get_field(  # type: ignore
                    field.name  # type: ignore
                ).verbose_name  # type: ignore
            self._related_name = self.MAPPING[token].related_name
            self._pre_function = self.MAPPING[token].pre
            self._post_function = self.MAPPING[token].post
        except KeyError:
            pass

        if not field and (token in self.DYNAMIC_FIELDS):
            field = Field(name=token)  # type: ignore
            self._verbose_name = self.DYNAMIC_FIELDS[field.name].verbose_name
            self._dynamic_field_function = self.DYNAMIC_FIELDS[field.name].function
            self._dynamic = True

        if not field:
            try:
                field = Machine._meta.get_field(token)  # type: ignore
                self._verbose_name = field.verbose_name  # type: ignore
            except FieldDoesNotExist:
                pass

        if not field:
            related_name = "__".join(token.split("__")[:-1])
            field_name = token.split("__")[-1]

            if related_name:
                for token, values in self.MAPPING.items():
                    if related_name == values.related_name:
                        if field_name == values.field.name:  # type: ignore
                            field = self.MAPPING[token].field  # type: ignore
                            self._related_name = related_name
                            self._verbose_name = self.MAPPING[token].verbose_name
                            self._pre_function = self.MAPPING[token].pre
                            self._post_function = self.MAPPING[token].post

        if not field:
            raise ValueError("Unknown field '{}'!".format(token))
        self._field = field  # type: ignore

    def __str__(self) -> str:
        return self.db_field_name

    def __repr__(self) -> str:
        if not self.is_dynamic:
            return "<{}: {}>".format(self.__class__.__name__, self.db_field_name)
        return "<{}: {} (dynamic)>".format(self.__class__.__name__, self.db_field_name)

    @classmethod
    def get_valid_field_names(cls) -> List[str]:
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
    def db_field_name(self) -> str:
        """Return a valid field name for querying the DB."""
        if self._related_name:
            field_name = "{}__{}".format(self._related_name, self._field.name)  # type: ignore
        else:
            field_name = self._field.name  # type: ignore

        if self._annotation is not None:
            field_name += self._annotation  # type: ignore

        return field_name  # type: ignore

    @property
    def related_name(self) -> str:
        """Return the related name of a `QueryField` object."""
        return self._related_name  # type: ignore

    @property
    def verbose_name(self) -> str:
        """Return the verbose name of a `QueryField` object."""
        if self._verbose_name.islower():  # type: ignore
            return self._verbose_name.capitalize()  # type: ignore
        return self._verbose_name  # type: ignore

    @property
    def null(self) -> bool:
        """Return if a `QueryField` object can be `NULL` in the DB."""
        return self._field.null  # type: ignore

    @property
    def is_dynamic(self) -> bool:
        """Return if a `QueryField` object is dynamic (non-database value) or not."""
        return self._dynamic

    def is_BooleanField(self) -> bool:
        """Check if a `QueryField` object is a boolean field."""
        return "BooleanField" in self._field.get_internal_type()  # type: ignore

    def is_CharField(self) -> bool:
        """Check if a `QueryField` object is a character field."""
        return "CharField" in self._field.get_internal_type()  # type: ignore

    def is_TextField(self) -> bool:
        """Check if a `QueryField` object is a character field."""
        return "TextField" in self._field.get_internal_type()  # type: ignore

    def is_ForeignKey(self) -> bool:
        """Check if a `QueryField` object is a foreign key."""
        return "ForeignKey" in self._field.get_internal_type()  # type: ignore

    def is_DateField(self) -> bool:
        """Check if a `QueryField` object is a date field."""
        return "DateField" in self._field.get_internal_type()  # type: ignore

    def is_DateTimeField(self) -> bool:
        """Check if a `QueryField` object is a datetime field."""
        return "DateTimeField" in self._field.get_internal_type()  # type: ignore

    def get_db_function_length(self) -> Tuple["QueryField", Dict[str, Length]]:
        """
        Return a tuple with a valid DB field name for querying string length and its corresponding
        DB function.

        Example:
            ('comment_length', Length('comment'))
        """
        field = QueryField(self.db_field_name + self.LENGTH_SUFFIX)
        return field, {field.db_field_name: Length(self.db_field_name)}

    @property
    def type(self) -> str:
        """Return fields type as string."""
        return self._field.get_internal_type()  # type: ignore

    @property
    def dynamic_field_function(self):  # type: ignore
        """
        Return a optional function for processing dynamic fields (non-database fields).

        If no dynamic function is defined, a simple lambda function is returned which simply
        returns the input value.
        """
        if self._dynamic_field_function:  # type: ignore
            return self._dynamic_field_function
        return lambda x: x  # type: ignore

    @property
    def pre_function(self):  # type: ignore
        """
        Return a optional pre-function.

        If no pre-function is defined, a simple lambda function is returned which simply returns
        the input value.
        """
        if self._pre_function:
            return self._pre_function
        return lambda x: x  # type: ignore

    @property
    def post_function(self):  # type: ignore
        """
        Return a optional post-function.

        If no post-function is defined, a simple lambda function is returned which simply returns
        the input value.
        """
        if self._post_function:
            return self._post_function
        return lambda x: x  # type: ignore


class APIQuery:
    class EmptyResult(Exception):
        pass

    OPERATORS = {
        "=": {
            "__default__": "__iexact",
            "DateTimeField": "",
            "ForeignKey": "",
        },
        "==": {
            "__default__": "__iexact",
            "DateTimeField": "",
            "ForeignKey": "",
        },
        "=~": {
            "__default__": "__icontains",
        },
        "=*": {
            "__default__": "__istartswith",
        },
        "!=": {
            "__default__": "__ne",
        },
        ">": {
            "__default__": "__gt",
        },
        ">=": {
            "__default__": "__gte",
        },
        "<": {
            "__default__": "__lt",
        },
        "<=": {
            "__default__": "__lte",
        },
    }

    AND = "and"
    OR = "or"
    WHERE = "where"

    def __init__(self, query_str: str) -> None:
        self._query_str = query_str.strip()
        self._query = None
        self._data: Optional[List[Dict[str, Any]]] = None
        self._fields: List[str] = []
        self._conditions: List[Tuple[QueryField, str, Union[bool, int]]] = []
        self._conjunctions: List[str] = []
        self._annotations: List[Dict[str, Length]] = []

    def _prepare_query(self) -> None:
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

            (
                self._conditions,
                self._conjunctions,
                self._annotations,
            ) = self._prepare_conditions(query[1])

        elif len(query) > 2:
            raise SyntaxError("Invalid syntax (multiple 'where' found)!")

    def _prepare_fields(self, fields_str: str) -> List[str]:
        """Strip query string in query fields."""
        fields: List[str] = []

        for token in fields_str.split(","):
            field = QueryField(token.strip())
            fields.append(field.db_field_name)

        return fields

    def _prepare_conditions(
        self, conditions_str: str
    ) -> Tuple[
        List[Tuple[QueryField, str, Union[bool, int]]],
        List[str],
        List[Dict[str, Length]],
    ]:
        """
        Assemble conditions.

        For single condition statements on character fields, annotations get added for string
        length comparing.

        Return:
            (
                ['(<field>', '__<op>', '<value>'), ...],
                ['and', 'or', ...],
                ['<field>_length', Length(<field>), ...]
            )

        Examples:
            where foo ...           -> [('foo', '', 'True'), ...]
            where !foo ...          -> [('foo', '', 'False'), ...]
            where foo =~ bar ...    -> [('foo', '__istartswith', 'bar'), ...]
            where comment ...       -> [('comment_length', '__gt', 0, ...]
        """
        conditions: List[Tuple[QueryField, str, Union[bool, int]]] = []
        conjunctions: List[str] = []
        annotations: List[Dict[str, Length]] = []
        condition: Tuple[QueryField, str, Union[bool, int]] = ()  # type: ignore
        state = -1

        tokens: List[str] = []
        for token in re.split(
            """ (?=(?:[^'"]|'[^']*'|"[^"]*")*$)""", conditions_str.strip()
        ):
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

                condition = (field,)  # type: ignore
                state = 0

            elif (
                state == -1
                and (not next_token or (next_token in {self.AND, self.OR}))
                and token not in {self.AND, self.OR}
            ):
                # single field without condition
                # where <field> and ...
                if token[0] == "!":
                    token = token[1:]
                    is_not = True
                else:
                    is_not = False

                field = QueryField(token)

                value: Union[bool, int]
                if field.null:
                    filter = "__isnull"
                    value = is_not

                elif field.is_BooleanField():
                    filter = ""
                    value = not is_not

                elif field.is_CharField() or field.is_TextField():
                    field, annotation = field.get_db_function_length()
                    annotations.append(annotation)
                    if is_not:
                        filter = ""
                        value = 0
                    else:
                        filter = "__gt"
                        value = 0

                else:
                    filter = "__isnull"
                    value = is_not

                condition = (field, filter, value)
                conditions.append(condition)

            elif state == 0:
                # where field <operator> value ...

                field = condition[0]

                try:
                    operator = self.OPERATORS[token][field.type]
                except KeyError:
                    operator = self.OPERATORS[token]["__default__"]

                condition = condition + (operator,)  # type: ignore
                state = 1

            elif state == 1:
                # where field = <value> ...
                # replace '%20' with whitespace; Example:
                #   query ... where inst_dist =* 'sles 12' -> 'sles%2012' -> 'sles 12'
                token = token.replace("%20", " ")

                if condition[0].is_DateTimeField() and token.lower() == "infinite":
                    if condition[1] == "__iexact":
                        # no timezone offset here
                        token = "9999-12-31 00:00:00"
                    else:
                        token = "9999-12-31 00:00+0000"

                condition = condition + (token,)  # type: ignore
                state = -1

                if condition[0].type == "ForeignKey" and condition[1] == "__ne":
                    # for foreign keys use '<' (__lt) and '>' (__gt) for '!='
                    conditions.append((condition[0], "__gt", condition[2]))
                    conjunctions.append(self.OR)
                    conditions.append((condition[0], "__lt", condition[2]))
                else:
                    conditions.append(condition)

            elif next_token and token == self.AND:
                conjunctions.append(self.AND)

            elif next_token and token == self.OR:
                conjunctions.append(self.OR)

            else:
                raise Exception("Invalid condition!")

        return conditions, conjunctions, annotations

    def _get_query(self) -> Q:
        """Return valid django model queries which can be piped into `filter()` method."""
        if self.has_conditions:
            if not self._conditions:
                raise Exception("Missing condition!")

            field, op, value = self._conditions[0]

            if field.is_dynamic:
                raise NotImplementedError(
                    "Non-database (dynamic) fields are not supported!"
                )

            query = Q(**{"{}{}".format(field.db_field_name, op): value})

            for i in range(0, len(self._conditions) - 1):
                field, op, value = self._conditions[i + 1]

                if field.is_dynamic:
                    raise NotImplementedError(
                        "Non-database (dynamic) fields are not supported!"
                    )

                try:
                    left = query
                    right = Q(**{"{}{}".format(field.db_field_name, op): value})
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

    def execute(
        self, user: Optional[Union[AbstractBaseUser, AnonymousUser]] = None
    ) -> None:
        """
        Execute requested query and stores the result.

        This method is responsible for preparing, executing and revising data from the DB.
        """
        self._prepare_query()
        self._apply_pre_functions()

        query = self._get_query()

        logger.debug("Execute query: %s", query)

        # set `user` in order to prevent search results including administrative systems
        queryset = Machine.search.get_queryset(user=user)  # type: ignore

        for annotation in self._annotations:
            queryset = queryset.annotate(**annotation)

        queryset = queryset.filter(query).distinct()

        if queryset:
            result = list(
                queryset.values(
                    *list(set(self._fields) - set(QueryField.DYNAMIC_FIELDS)) + ["pk"]
                )
            )
        else:
            raise self.EmptyResult("No results found!")

        if not result:
            raise self.EmptyResult("No results found!")

        self._data = result
        self._data = self._add_dynamic_fields(self._data)
        self._data = self._apply_post_functions(self._data)

    def _add_dynamic_fields(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fields which are non-database fields needs to be queried and added separately using
        the primary key. If the primary key wasn't requested, remove it.
        """
        for machine in rows:
            for dynamic_field, _values in QueryField.DYNAMIC_FIELDS.items():
                field = QueryField(dynamic_field)
                if field.db_field_name in self._fields:
                    machine[field.db_field_name] = field.dynamic_field_function(  # type: ignore
                        machine["pk"]
                    )

        # removal needs to be done here due to multiple pk lookups above
        for machine in rows:
            if "pk" not in self._fields:
                machine.pop("pk", None)

        return rows

    def _apply_pre_functions(self) -> None:
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
                field.pre_function(value),  # type: ignore
            )

    def _apply_post_functions(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply post-functions on each result row."""
        for row in rows:
            for field, value in row.items():
                if value is None:
                    continue
                qfield = QueryField(field)
                row[qfield.db_field_name] = qfield.post_function(value)  # type: ignore

        return rows

    @property
    def has_conditions(self) -> bool:
        return bool(self._conditions)

    @property
    def data(self):
        return self._data

    def get_theader(self) -> List[Dict[str, str]]:
        """
        Return fields for table header with verbose name specified in the model or manually in
        class `QueryField`.
        """
        result: List[Dict[str, str]] = []

        for token in self._fields:
            field = QueryField(token)
            result.append({field.db_field_name: field.verbose_name})

        return result

    @staticmethod
    def get_tab_completion_options() -> List[str]:
        """Return fields, operators, etc. for tab completion as list."""
        options = QueryField.get_valid_field_names()
        options += list(APIQuery.OPERATORS.keys())
        options += [APIQuery.WHERE, APIQuery.AND, APIQuery.OR, "infinite"]

        return options
