"""
Utility functions for distribution version parsing and risk detection.

This module provides functions to parse SLES versions and detect risky
setup choices that may affect boot order.
"""

import re
from typing import Optional, Tuple


def parse_sles_version(distribution: str) -> Optional[Tuple[int, int]]:
    """
    Parse SLES version from distribution string.

    Only parses regular SLES versions (SLE-15-SP3, SLES-12-SP4).
    SLE-Micro and SL-Micro versions are not parsed and return None.

    Args:
        distribution: Distribution name (e.g., "SLE-15-SP3-Server-LATEST:install-auto")

    Returns:
        Tuple of (major, service_pack) or None if not regular SLES or unparseable

    Examples:
        >>> parse_sles_version("SLE-15-SP3-Server-LATEST:install")
        (15, 3)
        >>> parse_sles_version("SLE-12-SP4-Server-LATEST")
        (12, 4)
        >>> parse_sles_version("SLE-Micro-5.5")
        None
        >>> parse_sles_version("SL-Micro-6.0")
        None
        >>> parse_sles_version("openSUSE-Leap-15.3")
        None
    """
    # Parse regular SLES pattern: SLE-15-SP3, SLES-12-SP4
    # Note: SLE-Micro and SL-Micro are NOT parsed here
    pattern = re.compile(r"^SLES?-(\d+)-SP(\d+)", re.IGNORECASE)
    match = pattern.match(distribution)

    if match:
        major = int(match.group(1))
        service_pack = int(match.group(2))
        return major, service_pack

    return None


def is_risky_sles_version(distribution: str) -> bool:
    """
    Check if SLES distribution is older than 15 SP3.

    SLES versions older than 15 SP3 may have boot order issues when
    automatic installation is performed with newer codestreams.
    All SLE-Micro and SL-Micro versions are considered safe.

    Args:
        distribution: Distribution name with or without profile

    Returns:
        True if SLES and version < 15 SP3, False otherwise
        (Returns False for non-SLES distributions and all Micro editions)

    Examples:
        >>> is_risky_sles_version("SLE-12-SP4-Server-LATEST")
        True
        >>> is_risky_sles_version("SLE-15-SP2-Server-LATEST:install")
        True
        >>> is_risky_sles_version("SLE-15-SP3-Server-LATEST")
        False
        >>> is_risky_sles_version("SLE-Micro-5.5")
        False
        >>> is_risky_sles_version("SL-Micro-6.0")
        False
        >>> is_risky_sles_version("SL-Micro-6.2")
        False
        >>> is_risky_sles_version("openSUSE-Leap-15.3")
        False
    """
    # Check for Micro versions first - all Micro versions are safe
    micro_pattern = re.compile(r"^SLE?-Micro-", re.IGNORECASE)
    if micro_pattern.match(distribution):
        return False

    # Parse regular SLES version
    version = parse_sles_version(distribution)

    if version is None:
        return False

    major, sp = version
    return (major < 15) or (major == 15 and sp < 3)


def is_manual_installation(profile: str) -> bool:
    """
    Check if profile requires manual installation.

    Manual installation profiles (:install, :install-ssh) can break boot
    order as they require manual configuration after OS installation.

    Args:
        profile: Full setup choice (e.g., "SLE-15-SP2:install")

    Returns:
        True if profile ends with :install or :install-ssh, False otherwise
        (Excludes :install-auto and :install-auto-ssh)

    Raises:
        ValueError: If the input format is malformed (empty string, empty
                   distribution/profile parts)

    Examples:
        >>> is_manual_installation("SLE-15-SP3:install")
        True
        >>> is_manual_installation("SLE-12-SP4:install-ssh")
        True
        >>> is_manual_installation("SLE-15-SP3:install-auto")
        False
        >>> is_manual_installation("SLE-15-SP3:install-auto-ssh")
        False
        >>> is_manual_installation("SLE-15-SP3-Server-LATEST")
        False
    """
    # Check for empty string
    if not profile:
        raise ValueError("Distribution format is incorrect: empty string")

    # No colon means no profile specified (not manual installation)
    if ":" not in profile:
        return False

    # Split and validate parts
    parts = profile.split(":", 1)
    distribution_part = parts[0]
    profile_part = parts[1]

    # Validate distribution and profile parts are not empty
    if not distribution_part:
        raise ValueError(
            f"Distribution format is incorrect: missing distribution part in '{profile}'"
        )

    if not profile_part:
        raise ValueError(
            f"Distribution format is incorrect: missing profile part in '{profile}'"
        )

    return profile_part in ("install", "install-ssh")


def needs_boot_order_warning(setup_choice: str) -> bool:
    """
    Check if setup choice requires boot order warning.

    A warning is needed when either:
    1. Distribution is SLES older than 15 SP3, OR
    2. Profile requires manual installation

    Args:
        setup_choice: Full setup choice (distribution:profile format)

    Returns:
        True if risky SLES version OR manual installation profile

    Raises:
        ValueError: If the input format is malformed (propagated from
                   is_manual_installation)

    Examples:
        >>> needs_boot_order_warning("SLE-12-SP4:install-auto")
        True
        >>> needs_boot_order_warning("SLE-15-SP4:install")
        True
        >>> needs_boot_order_warning("SLE-12-SP4:install")
        True
        >>> needs_boot_order_warning("SLE-15-SP4:install-auto")
        False
        >>> needs_boot_order_warning("openSUSE-Leap:install")
        False
    """
    return is_risky_sles_version(setup_choice) or is_manual_installation(setup_choice)
