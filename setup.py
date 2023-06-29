#!/usr/bin/env python

import os
from glob import glob

from setuptools import find_packages, setup

logpath = os.environ.get('LOG_PATH', "/var/log/orthos2")
db_path = os.environ.get('DB_PATH', "/var/lib/orthos2")
tmpfilespath = os.environ.get('TMPFILES_PATH', "/usr/lib/tmpfiles.d")
execpath = os.environ.get('EXEC_PATH', "/usr/lib/orthos2")
# Directory for package specific data
datapath = os.environ.get('DATA_PATH', "/usr/share/orthos2")
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
            ("/etc/nginx/conf.d", ["wsgi/orthos2_nginx.conf"]),
            ("/etc/logrotate.d", ["logrotate/orthos2"]),
            ("%s/scripts" % execpath, glob("orthos2/scripts/*")),
            ("/usr/bin", glob("orthos2/bin/*")),
            # orthos2 data files in /usr/share/orthos2
            ("/etc/orthos2", ["wsgi/orthos2.ini", "wsgi/settings"]),
            ("%s/fixtures/data" % datapath,
                glob("orthos2/data/fixtures/*.json")),
            ("%s/fixtures/taskmanager" % datapath,
                glob("orthos2/taskmanager/fixtures/*.json")),
            ("%s/fixtures/frontend/tests" % datapath,
                glob("orthos2/frontend/tests/fixtures/*.json")),
            ("%s/fixtures/utils/tests" % datapath,
                glob("orthos2/utils/tests/fixtures/*.json")),
            # tmpfiles.d -> renaming here is ugly, better use a subdirectory in repo
            ("%s" % tmpfilespath, ["service/tmpfiles.d/orthos2.conf"]),
            ("%s" % unitpath, ["service/orthos2.service",
                               "service/orthos2_taskmanager.service",
                               "service/orthos2_debug.service",
                               "service/orthos2.socket"]),
            # Empty directory creation
            ("%s" % logpath, []),
            ("%s" % db_path, []),
            ("%s/.ssh" % db_path, []),
            ("%s/archiv" % db_path, []),
            ("%s/database" % db_path, []),
            ("%s/orthos-vm-images" % db_path, []),
            ("/run/orthos2", [])
        ]
    )
