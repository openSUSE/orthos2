'''
This code came from utils/machinechecks get_hardware_information()
which invoked self made shell scripts.
This function/module will replace get_hardware_information by
passing ansible collected data instead of self called functions
'''

import os
import shutil
import glob
import threading
import logging
import json
from datetime import datetime

from django.template.loader import render_to_string

from orthos2.taskmanager.models import Task
from orthos2.data.models import Machine
from orthos2.utils.misc import normalize_ascii
from orthos2.utils.misc import execute

logger = logging.getLogger('tasks')


class Ansible(Task):

    data_dir = "/run/orthos2/ansible"
    data_dir_lastrun = "/run/orthos2/ansible_lastrun"
    data_dir_archive = "/run/orthos2/ansible_archive"
    facts_dir = "/usr/lib/orthos2/ansible"

    def __init__(self, machines: dict):
        """
        param machines: List of machines (strings) to scan via ansible
        """
        self.machines = machines

        self.thread_id = threading.current_thread().ident
        self.inventory_yml = os.path.join(Ansible.facts_dir, "inventory.yml")
        self.inventory_template = os.path.join(Ansible.facts_dir, "inventory.template")

    def render_inventory(self):
        """
        Creates an ansible inventory file from the template Ansible.inventory_yml
        and fills it with machines to scan
        """
        rendered = render_to_string(self.inventory_template, {"machine_list": self.machines})
        with open(self.inventory_yml, "w") as i_file:
            i_file.write(rendered)

    def execute(self):
        self.render_inventory()
        command = '/usr/bin/ansible-playbook -i {dir}/inventory.yml {dir}/site.yml'.format(dir=Ansible.facts_dir)
        stdout, stderr, returncode = execute(command)
        logger.debug("Calling: %s - %d", command, returncode)
        logger.debug("ansible: %s - %s - %s", stdout, stderr, returncode)
        files = self.get_json_filelist()
        missing = list(set(self.machines) - set(files))
        if missing:
            logger.warning("Cannot scan machines %s via ansible, missing json file in %s",
                           self.machines, Ansible.data_dir)
        success = []
        fail = []
        for fqdn in files:
            try:
                Ansible.store_machine_info(fqdn)
                success.append(fqdn)
            except Exception:
                logger.exception("Could not store ansible data of host %s", fqdn)
                fail.append(fqdn)
            logger.info("Successfully scanned via ansible: %s", success)
        if fail:
            logger.warning("Exceptions caught during scan for these hosts: %s", fail)
        # Copy json files from ../ansible to ../ansible_archive
        for file in glob.glob(Ansible.data_dir + "/*.json"):
            shutil.copy(file, Ansible.data_dir_archive)
        # Move ../ansible to ../ansible_lastrun
        shutil.rmtree(Ansible.data_dir_lastrun)
        shutil.move(Ansible.data_dir, Ansible.data_dir_lastrun)
        os.mkdir(Ansible.data_dir)

    def get_json_filelist(self) -> list:
        """
        Returns the list of machines for which json files have been
        created via ansible scan (.json suffix removed)
        """
        res_files = []
        for _subdir, _dirs, files in os.walk(Ansible.data_dir):
            for jfile in files:
                if jfile.endswith(".json"):
                    res_files.append(jfile[:-len(".json")])
        return res_files

    @staticmethod
    def get_ansible_data(machine_fqdn: str, try_lastruns=False):

        ans_file = os.path.join(Ansible.data_dir, machine_fqdn + '.json')
        if not os.path.isfile(ans_file):
            if not try_lastruns:
                logger.exception("json file %s does not exist", ans_file)
                return None
            else:
                ans_file = os.path.join(Ansible.data_dir_lastrun, machine_fqdn + '.json')
                if not os.path.isfile(ans_file):
                    ans_file = os.path.join(Ansible.data_dir_archive, machine_fqdn + '.json')
                    if not os.path.isfile(ans_file):
                        logger.exception("json file %s does not exist", ans_file)
                        return None
        try:
            with open(ans_file, 'r') as json_file:
                ansible_machine = json.load(json_file)
        except Exception as e:
            logger.exception("Could not load ansible json file %s - %s", ans_file, repr(e))
            return None

        return ansible_machine

    @staticmethod
    def store_machine_info(machine_fqdn: str):

        ansible_machine = Ansible.get_ansible_data(machine_fqdn)
        if not ansible_machine:
            return
        db_machine = Machine.objects.get(fqdn=machine_fqdn)

        Ansible.write_ansible_local(db_machine, ansible_machine)
        db_machine.save()

    @staticmethod
    def print_machine_info(machine_fqdn: str):
        """
        This is only a debug function which can be used via runscript interface
        Example:
        manage runscript show_machine_info --script-args lammermuir.arch.suse.de  |less
        """
        db_machine = Machine.objects.get(fqdn=machine_fqdn)
        if not db_machine:
            print("Machine: %s does not exist" % machine_fqdn)
            return
        # # prints all non magic attributes of a machine
        db_machine_attributes = [attribute for attribute in dir(db_machine)
                                 if not attribute.startswith('_')]
        for db_machine_attribute in db_machine_attributes:
            try:
                print(f"db_machine.{db_machine_attribute} = {getattr(db_machine, db_machine_attribute)}")
            except Exception:
                continue

    @staticmethod
    def print_ansible_info(machine_fqdn: str):
        """
        This is only a debug function which can be used via runscript interface
        Example:
        manage runscript show_ansible_info --script-args lammermuir.arch.suse.de  |less
        """

        ansible_machine = Ansible.get_ansible_data(machine_fqdn, try_lastruns=True)
        if not ansible_machine:
            return
        exclude_keys = ["_ansible_facts_gathered", "ansible_local"]
        for key in ansible_machine:
            if key in exclude_keys:
                continue
            print(key, '->', ansible_machine[key])
        return

    # def get_hardware_information(fqdn):
    @staticmethod
    def write_ansible_local(db_machine, ansible_machine):
        """
        Write ansible information retrieved from a json file to the system.
        For developing/debugging this interface can directly be use
        (without doing a rescan of the remote machine) via e.g.
        manage runscript store_machine_info --script-args lammermuir.arch.suse.de
        This can be useful if one wants to assign data which was already via ansible
        to the correct database fields here.
        """

        db_machine.fqdn = ansible_machine.get("fqdn", "")

        # Amount of real CPU sockets
        db_machine.cpu_physical = ansible_machine.get("processor_count", 1)
        # Amount of all CPU cores (sockets * cores_per_socket)
        db_machine.cpu_cores = ansible_machine.get("processor_cores", 1) * db_machine.cpu_physical
        # Amount of all CPU threads (All CPU cores * threads_per_core)
        db_machine.cpu_threads = db_machine.cpu_cores * ansible_machine.get("processor_threads_per_core", 1)
        # db_machine.cpu_model =
        # db_machine.cpu_flags = # --> check if in ansible, else create facts file
        # db_machine.cpu_speed =
        # db_machine.cpu_id =
        db_machine.ram_amount = int(ansible_machine.get("memtotal_mb", 0))
        # db_machine.disk_primary_size = # sectors * sector_size der 1. platte (in bytes).
        # danach hwinfo --disk entfernen.
        # db_machine.disk_type =

        # Need extra readonly commandline field
        # k_opts = ansible_machine.get("cmdline", 0)
        # if k_opts:
        #    db_machine.kernel_options = " ".join(['%s=%s' % (key,value) for key, value in k_opts.items()])
        db_machine.lsmod = normalize_ascii("".join(ansible_machine.get("ansible_local", {}).get("lsmod", {}).get(
                                           "noargs", {}).get("stdout", "")))
        db_machine.lspci = normalize_ascii("".join(ansible_machine.get("lspci", {}).get("-vvv -nn", {}).get(
                                           "stdout", "")))
        last = ansible_machine.get("ansible_local", {}).get("last", {}).get("latest", {}).get("stdout", "")
        db_machine.last = last[0:8] + last[38:49] if len(last) > 49 else ""
        db_machine.hwinfo = normalize_ascii("".join(ansible_machine.get("ansible_local", {}).get("hwinfo", {}).get(
                                            "full", {}).get("stdout", "")))
        db_machine.dmidecode = normalize_ascii("".join(ansible_machine.get("ansible_local", {}).get(
                                               "dmidecode", {}).get("noargs", {}).get("stdout", "")))
        db_machine.dmesg = normalize_ascii("".join(ansible_machine.get("ansible_local", {}).get("dmesg", {}).get(
                                           "-xl", {}).get("stdout", "")))
        db_machine.lsscsi = normalize_ascii("".join(ansible_machine.get("ansible_local", {}).get(
                                            "lsscsi", {}).get("-s", {}).get("stdout", "")))
        db_machine.lsusb = normalize_ascii("".join(ansible_machine.get("ansible_local", {}).get(
                                           "lsusb", {}).get("noargs", {}).get("stdout", "")))
        db_machine.ipmi = "IPMI" in db_machine.dmidecode

        try:
            bios_date = ansible_machine.get("bios_date", None)
            if bios_date == "NA":
                bios_date = None
            if bios_date:
                # Django date fields must be in "%Y-%m-%d" format
                db_machine.bios_date = datetime.strptime(bios_date, "%m/%d/%Y").strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            logger.exception("Could not parse bios date [%s]", db_machine.fqdn)

        db_machine.bios_version = ansible_machine.get("bios_version", "")
    # ------------------------------

    # db_machine.vm_capable =  # set when nice way to do so is found
    # db_machine.efi =  # set when nice way to do so is found

    # db_machine.serial_number # do not set
    # db_machine.architecture # do not set
    # db_machine.mac_address #  do not set

    # db_machine.__ipv4 # do not set (yet)
    # db_machine.__ipv6 # do not set (yet)

    '''
    attributes that can probaby be mapped easily/directly:
    db_machine.architecture = ansible_machine.get("architecture")
    db_machine.efi
    db_machine.cpu_id
    db_machine.cpu_model

    attributes where its values probably need to be edited before assigning:

    db_machine.disk_primary_size =
    db_machine.disk_type =
    db_machine.vm_capable =
    db_machine.cpu_flags =
    db_machine.cpu_physical.cpu_speed =

    db_machine.efi =
    db_machine.ipmi =
    db_machine.hwinfo =
    db_machine.dmidecode =
    db_machine.lspci =
    '''
