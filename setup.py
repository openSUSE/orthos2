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
    with open("README.md", "r") as readme:
        long_description = readme.read()

    setup(
        name="orthos2",
        version="1.19",
        description="Machine administration server",
        long_description=long_description,
        long_description_content_type="text/markdown",
        author="orthos team",
        url="https://github.com/openSUSE/orthos2",
        license="GPLv2+",
        setup_requires=[],
        install_requires=list(requires()),
        packages=find_packages(exclude=["*tests*"]),
        include_package_data=True,
    )
