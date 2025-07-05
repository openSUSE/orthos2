"""
This module contains all logic to set up a new machine via PXE.
"""

import collections
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from django import forms

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine

logger = logging.getLogger("views")


class SetupMachineForm(forms.Form):
    """
    Form to set up a new machine via PXE.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        machine: "Machine" = kwargs.pop("machine", None)
        domain = machine.fqdn_domain

        architecture = machine.architecture.name
        """
        Change choice html field here (domain.get_setup_records(..., grouped=True)
        grouped=True
           SLE-12-SP4-Server-LATEST
               install
               install-auto
               install-auto-ssh
           SLE-12-SP5-Server-LATEST
               install
               install-auto
               ...

        grouped=False
           SLE-12-SP4-Server-LATEST:install
           SLE-12-SP4-Server-LATEST:install-auto
           SLE-12-SP4-Server-LATEST:install-auto-ssh
           SLE-12-SP5-Server-LATEST:install
           SLE-12-SP5-Server-LATEST:install-auto
           ...
        """
        records = domain.get_setup_records_grouped(architecture)
        logger.debug(
            "Setup choices for %s.%s [%s]:\n%s\n",
            machine,
            domain,
            architecture,
            records,
        )

        super(SetupMachineForm, self).__init__(*args, **kwargs)

        self.fields["setup"].choices = self.get_setup_select_choices(records)  # type: ignore
        logger.debug(
            "Setup choicen for %s.%s [%s]:\n%s\n",
            machine,
            domain,
            architecture,
            self.fields["setup"].choices,  # type: ignore
        )

    def get_setup_select_choices(self, records: Dict[str, List[str]]):
        setup_records: List[Tuple[Optional[str], str]] = []
        groups: Dict[str, Tuple[Tuple[str, str], ...]] = collections.OrderedDict()

        if isinstance(records, list):
            for record in records:
                setup_records.append((record, record))

        elif isinstance(records, collections.OrderedDict):
            for distribution, record_group in records.items():

                for record in record_group:
                    option = record
                    value = distribution + ":" + record
                    if distribution not in groups.keys():
                        groups[distribution] = ((value, option),)
                    else:
                        groups[distribution] += ((value, option),)

            for distribution, record_group in groups.items():
                setup_records.append((distribution, record_group))  # type: ignore

        if not setup_records:
            setup_records.append((None, "no setup records available"))

        return setup_records

    setup = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
    )
