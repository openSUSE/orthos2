"""
This test module is verifying the get_installations.sh shell script that detects the operating system on a given target
system. It is used in machinechecks.py:get_installations(fqdn: str) and provides data to users in the Web UI what OSes
are installed on a given system.
"""

import subprocess
from pathlib import Path

import pytest

# Resolve paths relative to this file
TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent.parent
SCRIPT_PATH = (
    PROJECT_ROOT / "meta" / "data" / "scripts" / "machine_get_installations.sh"
)
DATA_DIR = PROJECT_ROOT / "utils" / "tests" / "machine_get_installations" / "data"


def get_distributions():
    print(DATA_DIR.exists())
    if not DATA_DIR.exists():
        return []
    # Only return directories that contain a DIST.txt file, matching the bash script's behavior
    return sorted(
        d.name for d in DATA_DIR.iterdir() if d.is_dir() and (d / "DIST.txt").is_file()
    )


@pytest.mark.parametrize("dist", get_distributions())
def test_machine_get_installations(dist):
    dist_dir = DATA_DIR / dist
    dist_txt_path = dist_dir / "DIST.txt"

    os_release = "/dev/null"
    issue = "/dev/null"
    suse_release = "/dev/null"

    if (dist_dir / "usr/lib/os-release").is_file() and (
        dist_dir / "usr/lib/issue.d/10-SUSE"
    ).is_file():
        os_release = "usr/lib/os-release"
        issue = "usr/lib/issue.d/10-SUSE"
    elif (dist_dir / "usr/lib/os-release").is_file() and (
        dist_dir / "usr/lib/issue.d/10-openSUSE.conf"
    ).is_file():
        os_release = "usr/lib/os-release"
        issue = "usr/lib/issue.d/10-openSUSE.conf"
    elif (dist_dir / "usr/lib/os-release").is_file() and (
        dist_dir / "etc/issue"
    ).is_file():
        os_release = "usr/lib/os-release"
        issue = "etc/issue"
    elif (dist_dir / "etc/os-release").is_file() and (
        dist_dir / "usr/lib/issue.d/10-SUSE"
    ).is_file():
        os_release = "etc/os-release"
        issue = "usr/lib/issue.d/10-SUSE"
    elif (dist_dir / "etc/os-release").is_file() and (dist_dir / "etc/issue").is_file():
        os_release = "etc/os-release"
        issue = "etc/issue"
    elif (dist_dir / "etc/SuSE-release").is_file() and (
        dist_dir / "etc/issue"
    ).is_file():
        os_release = "/dev/null"
        issue = "etc/issue"
        suse_release = "etc/SuSE-release"
    else:
        pytest.fail(f"{dist} lacks os-release/issue files")

    cmd = [
        str(SCRIPT_PATH),
        "--dist-debug",
        "--os-release",
        os_release,
        "--issue",
        issue,
        "--suse-release",
        suse_release,
    ]

    result = subprocess.run(cmd, cwd=dist_dir, capture_output=True, text=True)

    assert result.returncode == 0, f"Script failed with error: {result.stderr}"

    expected_output = dist_txt_path.read_text()

    assert result.stdout == expected_output
