
from setuptools import setup, find_packages
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
        install_requires=[
            "django",
            "django-extensions",
            "paramiko",
            "djangorestframework",
            "validators",
            "netaddr"
        ],
        packages=find_packages(exclude=["*tests*"]),
        data_files=[
            ("/etc/nginx/conf.d",  ["orthos2_nginx.conf"])
        ]
    )
