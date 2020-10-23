#!/usr/bin/env python

from setuptools import find_packages, setup
import os
from glob import glob

logpath = os.environ.get('LOG_PATH', "/var/log")
tmpfilespath = os.environ.get('TMPFILES_PATH', "/usr/lib/tmpfiles.d")
# Directory for package specific executables not exposed
# to the world via /bin or /sbin
execpath = os.environ.get('EXEC_PATH',  "/usr/lib")
# Directory for package specific data
datapath = os.environ.get('DATA_PATH', "/usr/share")
unitpath = os.environ.get('UNIT_PATH', "/usr/lib/systemd/system")


def requires(filename='requirements.txt'):
    """Returns a list of all pip requirements

    :param filename: the Pip requirement file
    (usually 'requirements.txt')
    :return: list of modules
    :rtype: list
    """
    with open(filename, 'r+t') as pipreq:
        for line in pipreq:
            line = line.strip()
            if not line or \
               line.startswith('#') or \
               line.startswith('-r'):
                continue
            yield line


if __name__ == "__main__":
    setup(

        name="orthos2",
        version='0.1',
        description="Machine administration server",
        long_description="""
        Orthos is the machine administration tool of the development network at SUSE.
        It is used for following tasks:

        getting the state of the machine
        overview about the hardware
        overview about the installed software (installations)
        reservation of the machines
        generating the DHCP configuration (via Cobbler)
        reboot the machines remotely
        managing remote (serial) consoles""",
        author="orthos team",
        url="https://github.com/openSUSE/orthos2",
        license="GPLv2+",
        setup_requires=[
        ],
        install_requires=list(requires()),
        packages=find_packages(exclude=["*tests*"]),
        scripts=[
            "cli/orthos2",
        ],
        data_files=[
            ("/etc/nginx/conf.d",  ["wsgi/orthos2_nginx.conf"]),
            # orthos2 internal binaries in /usr/lib/orthos2
            ("%s/orthos2" % execpath, glob("orthos2/bin/*")),
            ("%s/orthos2/wsgi" % execpath, ["wsgi/orthos2.py"]),
            # orthos2 data files in /usr/share/orthos2
            ("/etc/orthos2", ["wsgi/orthos2.ini", "wsgi/setttings"]),
            ("%s/orthos2/fixtures/data" % datapath,
                glob("orthos2/data/fixtures/*.json")),
            ("%s/orthos2/fixtures/taskmanager" % datapath,
                glob("orthos2/taskmanager/fixtures/*.json")),
            ("%s/orthos2/fixtures/frontend/tests" % datapath,
                glob("orthos2/frontend/tests/fixtures/*.json")),
            ("%s/orthos2/fixtures/utils/tests" % datapath,
                glob("orthos2/utils/tests/fixtures/*.json")),
            # tmpfiles.d -> renaming here is ugly, better use a subdirectory in repo
            ("%s" % tmpfilespath, ["service/tmpfiles.d/orthos2.conf"]),
            ("%s" % unitpath, ["service/orthos2.service",
                               "service/orthos2_taskmanager.service",
                               "service/orthos2.socket"]),
            # Empty directory creation
            ("%s/orthos2" % logpath, []),
            ("/run/orthos2",         [])
        ]
    )
