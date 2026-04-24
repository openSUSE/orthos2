"""
This module contains all logic to set up a new machine via PXE.
"""

import collections
import json
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

        # Store records for JSON export to template
        self.records = records

        # Populate distro and profile fields
        if isinstance(records, collections.OrderedDict):
            # Build distro choices
            distro_choices = [("", "Select a distribution...")]
            distro_choices.extend([(distro, distro) for distro in records.keys()])
            self.fields["distro"].choices = distro_choices  # type: ignore

            # Build profile choices (all profiles from all distros for initial load)
            profile_choices = [("", "Select a profile...")]
            all_profiles = set()
            for profiles in records.values():
                all_profiles.update(profiles)
            profile_choices.extend(
                [(profile, profile) for profile in sorted(all_profiles)]
            )
            self.fields["profile"].choices = profile_choices  # type: ignore
        else:
            # Fallback for non-grouped records (shouldn't happen based on current code)
            self.fields["distro"].choices = [("", "No distributions available")]  # type: ignore
            self.fields["profile"].choices = [("", "No profiles available")]  # type: ignore

        logger.debug(
            "Distro choices for %s.%s [%s]:\n%s\n",
            machine,
            domain,
            architecture,
            self.fields["distro"].choices,  # type: ignore
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

    distro = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
        label="Distribution",
    )

    profile = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
        label="Profile",
    )

    confirm_risky_setup = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="I understand this setup may require manual boot order configuration",
        help_text="This distribution or installation method may leave the machine in an unbootable state.",
    )

    def clean(self) -> Optional[Dict[str, Any]]:
        """Validate that risky setups are confirmed."""
        from orthos2.utils.distribution import needs_boot_order_warning

        cleaned_data = super().clean()
        if cleaned_data is None:
            return None
        distro = cleaned_data.get("distro")
        profile = cleaned_data.get("profile")
        confirmed = cleaned_data.get("confirm_risky_setup", False)

        # Combine distro and profile into setup choice for backward compatibility
        if distro and profile:
            setup_choice = f"{distro}:{profile}"
            cleaned_data["setup"] = setup_choice

            try:
                if needs_boot_order_warning(setup_choice):
                    if not confirmed:
                        raise forms.ValidationError(
                            "This setup choice requires manual confirmation due to potential boot order risks. "
                            "Please check the confirmation box to proceed."
                        )
            except ValueError as e:
                raise forms.ValidationError(f"Invalid setup choice format: {e}")

        return cleaned_data

    def get_records_json(self) -> str:
        """Return grouped records as JSON for JavaScript."""
        return json.dumps(self.records if hasattr(self, "records") else {})
