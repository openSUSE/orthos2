#!/usr/bin/env python

from setuptools import find_packages, setup


def requires(filename: str = "requirements.txt"):
    """Returns a list of all pip requirements

    :param filename: the Pip requirement file
    (usually 'requirements.txt')
    :return: list of modules
    :rtype: list
    """
    with open(filename, "r+t") as pipreq:
        for line in pipreq:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-r"):
                continue
            yield line


if __name__ == "__main__":
    setup(
        name="orthos2",
        version="0.1",
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
        setup_requires=[],
        install_requires=list(requires()),
        packages=find_packages(exclude=["*tests*"]),
        include_package_data=True,
        scripts=[
            "cli/orthos2",
        ],
    )
