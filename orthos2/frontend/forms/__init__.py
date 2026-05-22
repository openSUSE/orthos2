"""
This module groups together all Django Forms that the application needs. Forms for the API should be living inside the
"orthos2.api.forms" package.
"""

from orthos2.frontend.forms.auth import RememberUsernameAuthenticationForm

__all__ = ["RememberUsernameAuthenticationForm"]
