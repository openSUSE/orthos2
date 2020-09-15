#!/usr/bin/env python

from setuptools import find_packages, setup


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
        long_description="Cobbler is a network install server. Cobbler supports PXE, virtualized installs, "
                         "and reinstalling existing Linux machines. The last two modes use a helper tool, 'koan', "
                         "that integrates with cobbler. There is also a web interface 'cobbler-web'. Cobbler's "
                         "advanced features include importing distributions from DVDs and rsync mirrors, automatic OS "
                         "installation templating, integrated yum mirroring, and built-in DHCP/DNS Management. "
                         "Cobbler has a XMLRPC API for integration with other applications.",
        author="Team Cobbler",
        author_email="cobbler.project@gmail.com",
        url="https://cobbler.github.io",
        license="GPLv2+",
        setup_requires=[
        ],
        install_requires=list(requires()),
        packages=find_packages(exclude=["*tests*"]),
        data_files=[
            # ("/etc/nginx/conf.d",  ["orthos2_nginx.conf"])
        ]
    )
