#!/usr/bin/python3

from django.apps import apps
from django.core.management.base import BaseCommand, CommandParser

from orthos2.utils.hostnamefinder import HostnameFinder


class Command(BaseCommand):
    help = "Find free hostnames\n"

    config = apps.get_app_config("data")
    queries = []

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.machinesonly = False

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('--domain', default="arch.suse.de", help="Domainname")
        parser.add_argument('--arch', default="x86_64", help="architecture")

    def handle(self, *args, **options):
        domain = options["domain"]
        arch = options["arch"]
        print("Checking for:")
        print("Domain: {}".format(domain))
        print("Architecture: {}".format(arch))
        print()
        finder = HostnameFinder.by_domain(domain, arch)
        if not finder:
            print("HostnameFinder not properly configured")
            return
        used, unused = finder.free_hostnames()
        print("Found {} used machines:\n{}".format(len(used), used))
        print("Found {} unused machine names:\n{}".format(len(unused), unused))
