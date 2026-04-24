"""
Pytest test cases for distribution utility functions.
"""

import pytest

from orthos2.utils.distribution import (
    is_manual_installation,
    is_risky_sles_version,
    needs_boot_order_warning,
    parse_sles_version,
)


class TestParseSlesVersion:
    """Test cases for parse_sles_version function."""

    @pytest.mark.parametrize(
        "distribution,expected",
        [
            # Regular SLES with SP notation
            ("SLE-15-SP3-Server-LATEST", (15, 3)),
            ("SLE-15-SP4-Server-LATEST", (15, 4)),
            ("SLE-15-SP5-Server-LATEST", (15, 5)),
            ("SLE-12-SP4-Server-LATEST", (12, 4)),
            ("SLE-12-SP5-Server-LATEST", (12, 5)),
            ("SLE-15-SP2-Server-LATEST", (15, 2)),
            # SLES variant (with extra 'S')
            ("SLES-15-SP3-Server-LATEST", (15, 3)),
            ("SLES-12-SP4-Server-LATEST", (12, 4)),
            # With profile suffix
            ("SLE-15-SP3-Server-LATEST:install", (15, 3)),
            ("SLE-15-SP3-Server-LATEST:install-auto", (15, 3)),
            ("SLE-12-SP4-Server-LATEST:install-ssh", (12, 4)),
            ("SLES-15-SP4:install-auto-ssh", (15, 4)),
            # Case insensitive
            ("sle-15-sp3-server-latest", (15, 3)),
            ("SLE-15-sp3-SERVER-LATEST", (15, 3)),
            # SLE-Micro versions (NOT parsed, return None)
            ("SLE-Micro-5.5", None),
            ("SLE-Micro-5.0", None),
            ("SLE-Micro-6.0", None),
            ("SLE-Micro-6.2", None),
            # SL-Micro versions (without 'E', also NOT parsed)
            ("SL-Micro-6.0", None),
            ("SL-Micro-6.2", None),
            ("SL-Micro-5.5", None),
            # Micro with profile suffix (still NOT parsed)
            ("SLE-Micro-5.5:install", None),
            ("SL-Micro-6.0:install-auto", None),
            # Case insensitive for Micro (still NOT parsed)
            ("sle-micro-5.5", None),
            ("SLE-MICRO-6.0", None),
            # Non-SLES distributions should return None
            ("openSUSE-Leap-15.3", None),
            ("openSUSE-Tumbleweed", None),
            ("Ubuntu-20.04", None),
            ("RHEL-8", None),
            ("Debian-11", None),
            ("Fedora-38", None),
            # Edge cases
            ("", None),
            ("SLE-Server-LATEST", None),  # Missing version
            ("SLE-15", None),  # Missing SP
            ("15-SP3", None),  # Missing SLE prefix
            ("SLE-15-3", None),  # Missing SP keyword
        ],
    )
    def test_parse_sles_version(self, distribution, expected):
        """Test parsing SLES versions from distribution strings."""
        assert parse_sles_version(distribution) == expected


class TestIsRiskySlesVersion:
    """Test cases for is_risky_sles_version function."""

    @pytest.mark.parametrize(
        "distribution,expected",
        [
            # Risky versions (< 15 SP3)
            ("SLE-12-SP1-Server-LATEST", True),
            ("SLE-12-SP2-Server-LATEST", True),
            ("SLE-12-SP3-Server-LATEST", True),
            ("SLE-12-SP4-Server-LATEST", True),
            ("SLE-12-SP5-Server-LATEST", True),
            ("SLE-15-SP0-Server-LATEST", True),
            ("SLE-15-SP1-Server-LATEST", True),
            ("SLE-15-SP2-Server-LATEST", True),
            ("SLES-12-SP4-Server-LATEST", True),
            ("SLES-15-SP2-Server-LATEST", True),
            # Risky with profile suffix
            ("SLE-12-SP4:install-auto", True),
            ("SLE-15-SP2:install", True),
            # Safe versions (>= 15 SP3)
            ("SLE-15-SP3-Server-LATEST", False),
            ("SLE-15-SP4-Server-LATEST", False),
            ("SLE-15-SP5-Server-LATEST", False),
            ("SLE-15-SP6-Server-LATEST", False),
            ("SLES-15-SP3-Server-LATEST", False),
            ("SLES-15-SP4-Server-LATEST", False),
            # Safe with profile suffix
            ("SLE-15-SP3:install", False),
            ("SLE-15-SP4:install-auto", False),
            # Micro versions (all safe - regardless of version number)
            ("SLE-Micro-5.0", False),
            ("SLE-Micro-5.5", False),
            ("SLE-Micro-6.0", False),
            ("SLE-Micro-6.2", False),
            ("SL-Micro-5.5", False),
            ("SL-Micro-6.0", False),
            ("SL-Micro-6.2", False),
            ("SLE-Micro-5.5:install", False),
            ("SL-Micro-6.2:install-auto", False),
            # Non-SLES distributions (safe - no warning)
            ("openSUSE-Leap-15.3", False),
            ("openSUSE-Tumbleweed", False),
            ("Ubuntu-20.04", False),
            ("RHEL-8", False),
            ("Debian-11", False),
            # Edge cases
            ("", False),
            ("invalid-distribution", False),
        ],
    )
    def test_is_risky_sles_version(self, distribution, expected):
        """Test detection of risky SLES versions."""
        assert is_risky_sles_version(distribution) == expected


class TestIsManualInstallation:
    """Test cases for is_manual_installation function."""

    @pytest.mark.parametrize(
        "profile,expected",
        [
            # Manual installation profiles (risky)
            ("SLE-15-SP3:install", True),
            ("SLE-15-SP4:install", True),
            ("SLE-12-SP4:install", True),
            ("SLE-15-SP3:install-ssh", True),
            ("SLE-12-SP4:install-ssh", True),
            ("SLES-15-SP3:install", True),
            ("SLE-Micro-5.5:install", True),
            ("SL-Micro-6.0:install-ssh", True),
            # Automatic installation profiles (safe)
            ("SLE-15-SP3:install-auto", False),
            ("SLE-15-SP4:install-auto", False),
            ("SLE-12-SP4:install-auto", False),
            ("SLE-15-SP3:install-auto-ssh", False),
            ("SLE-12-SP4:install-auto-ssh", False),
            ("SLES-15-SP3:install-auto", False),
            ("SLE-Micro-5.5:install-auto", False),
            ("SL-Micro-6.0:install-auto-ssh", False),
            # No profile suffix (safe)
            ("SLE-15-SP3-Server-LATEST", False),
            ("SLE-12-SP4-Server-LATEST", False),
            ("SLES-15-SP3", False),
            ("SLE-Micro-5.5", False),
            # Other profiles (safe)
            ("SLE-15-SP3:custom-profile", False),
            ("SLE-15-SP3:rescue", False),
            ("SLE-15-SP3:minimal", False),
            # No colon cases (valid - no profile specified)
            ("install", False),  # No colon, not manual installation
            ("install-ssh", False),  # No colon, not manual installation
            ("SLE-15-SP3-Server-LATEST", False),  # No colon, full distribution name
            # Ensure substring matching doesn't false positive
            ("SLE-15-SP3:my-install", False),
            ("SLE-15-SP3:install-something", False),
            ("SLE-15-SP3:reinstall", False),
        ],
    )
    def test_is_manual_installation(self, profile, expected):
        """Test detection of manual installation profiles."""
        assert is_manual_installation(profile) == expected

    @pytest.mark.parametrize(
        "profile,error_msg",
        [
            ("", "empty string"),
            (":install", "missing distribution part"),
            (":", "missing profile part"),
            ("SLE-15-SP3:", "missing profile part"),
        ],
    )
    def test_is_manual_installation_raises_on_malformed_input(self, profile, error_msg):
        """Test that malformed inputs raise ValueError."""
        with pytest.raises(ValueError, match="Distribution format is incorrect"):
            is_manual_installation(profile)


class TestNeedsBootOrderWarning:
    """Test cases for needs_boot_order_warning function."""

    @pytest.mark.parametrize(
        "setup_choice,expected,reason",
        [
            # Risky SLES version alone
            ("SLE-12-SP4:install-auto", True, "old SLES version"),
            ("SLE-15-SP2:install-auto", True, "old SLES version"),
            ("SLE-12-SP5:install-auto-ssh", True, "old SLES version"),
            # Manual installation alone (on safe SLES)
            ("SLE-15-SP4:install", True, "manual installation"),
            ("SLE-15-SP5:install-ssh", True, "manual installation"),
            ("SLES-15-SP3:install", True, "manual installation"),
            ("SLE-Micro-5.5:install", True, "manual installation"),
            # Both conditions (old SLES + manual)
            ("SLE-12-SP4:install", True, "both old SLES and manual"),
            ("SLE-15-SP2:install-ssh", True, "both old SLES and manual"),
            ("SLES-12-SP5:install", True, "both old SLES and manual"),
            # Safe configurations (new SLES + automatic)
            ("SLE-15-SP3:install-auto", False, "safe SLES + auto install"),
            ("SLE-15-SP4:install-auto", False, "safe SLES + auto install"),
            ("SLE-15-SP5:install-auto-ssh", False, "safe SLES + auto install"),
            ("SLES-15-SP4:install-auto", False, "safe SLES + auto install"),
            ("SLE-Micro-5.5:install-auto", False, "Micro + auto install"),
            ("SL-Micro-6.0:install-auto-ssh", False, "Micro + auto install"),
            # Safe SLES without profile
            ("SLE-15-SP4-Server-LATEST", False, "safe SLES no profile"),
            ("SLE-15-SP3-Server-LATEST", False, "safe SLES no profile"),
            # Non-SLES distributions
            ("openSUSE-Leap:install", True, "non-SLES manual"),
            ("openSUSE-Leap:install-ssh", True, "non-SLES manual"),
            ("Ubuntu-20.04:install", True, "non-SLES manual"),
            ("openSUSE-Leap:install-auto", False, "non-SLES auto"),
            # Non-SLES without profile
            ("openSUSE-Leap-15.3", False, "non-SLES no profile"),
            ("Ubuntu-20.04", False, "non-SLES no profile"),
            # Valid but no warning needed
            ("invalid-distribution", False, "invalid distribution"),
        ],
    )
    def test_needs_boot_order_warning(self, setup_choice, expected, reason):
        """Test combined warning logic with reason annotations."""
        assert (
            needs_boot_order_warning(setup_choice) == expected
        ), f"Failed for: {reason}"

    @pytest.mark.parametrize(
        "setup_choice",
        ["", ":install", ":", "SLE-15-SP3:"],
    )
    def test_needs_boot_order_warning_raises_on_malformed_input(self, setup_choice):
        """Test that malformed inputs raise ValueError."""
        with pytest.raises(ValueError, match="Distribution format is incorrect"):
            needs_boot_order_warning(setup_choice)


class TestEdgeCasesAndIntegration:
    """Additional edge case and integration tests."""

    def test_parse_handles_whitespace(self):
        """Test that parsing handles distributions with extra whitespace."""
        # This should still return None as whitespace breaks the pattern
        assert parse_sles_version(" SLE-15-SP3") is None

    def test_case_insensitive_throughout(self):
        """Test case insensitivity across all functions."""
        # parse_sles_version
        assert parse_sles_version("sle-15-sp3") == (15, 3)
        assert parse_sles_version("SLE-15-SP3") == (15, 3)
        assert parse_sles_version("Sle-15-Sp3") == (15, 3)

        # is_risky_sles_version
        assert is_risky_sles_version("sle-12-sp4") is True
        assert is_risky_sles_version("SLE-12-SP4") is True
        assert is_risky_sles_version("Sle-15-Sp2") is True

        # Micro versions (all return None)
        assert parse_sles_version("sle-micro-5.5") is None
        assert parse_sles_version("SLE-MICRO-5.5") is None
        assert is_risky_sles_version("sle-micro-6.2") is False
        assert is_risky_sles_version("SLE-MICRO-6.2") is False

    def test_boundary_conditions(self):
        """Test exact boundary at SLES15 SP3."""
        # SP2 is risky
        assert is_risky_sles_version("SLE-15-SP2") is True

        # SP3 is safe
        assert is_risky_sles_version("SLE-15-SP3") is False

        # SP4 is safe
        assert is_risky_sles_version("SLE-15-SP4") is False

    def test_profile_extraction(self):
        """Test that profile extraction works correctly."""
        # Manual profiles
        assert is_manual_installation("SLE-15-SP3:install") is True
        assert is_manual_installation("SLE-15-SP3:install-ssh") is True

        # Auto profiles should not trigger
        assert is_manual_installation("SLE-15-SP3:install-auto") is False
        assert is_manual_installation("SLE-15-SP3:install-auto-ssh") is False

    def test_micro_versions_not_parsed(self):
        """Test that Micro versions are NOT parsed (return None)."""
        # All Micro versions return None from parse_sles_version
        assert parse_sles_version("SLE-Micro-5.0") is None
        assert parse_sles_version("SLE-Micro-5.5") is None
        assert parse_sles_version("SLE-Micro-6.0") is None
        assert parse_sles_version("SLE-Micro-6.2") is None
        assert parse_sles_version("SL-Micro-6.0") is None
        assert parse_sles_version("SL-Micro-6.2") is None

        # But all Micro versions are still safe (no version warning)
        assert is_risky_sles_version("SLE-Micro-5.0") is False
        assert is_risky_sles_version("SLE-Micro-6.2") is False
        assert is_risky_sles_version("SL-Micro-6.0") is False
        assert is_risky_sles_version("SL-Micro-6.2") is False

    def test_warning_combinations(self):
        """Test various combinations that should trigger warnings."""
        # Old SLES + auto install = warning
        assert needs_boot_order_warning("SLE-12-SP4:install-auto") is True

        # New SLES + manual install = warning
        assert needs_boot_order_warning("SLE-15-SP4:install") is True

        # Old SLES + manual install = warning (both conditions)
        assert needs_boot_order_warning("SLE-12-SP4:install") is True

        # New SLES + auto install = no warning
        assert needs_boot_order_warning("SLE-15-SP4:install-auto") is False

        # Micro + manual = warning (manual always warns on SLES)
        assert needs_boot_order_warning("SLE-Micro-5.5:install") is True

        # Micro + auto = no warning
        assert needs_boot_order_warning("SLE-Micro-5.5:install-auto") is False
