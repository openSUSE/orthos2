'''
This code came from utils/machinechecks get_hardware_information()
which invoked self made shell scripts.
This function/module will replace get_hardware_information by
passing ansible collected data instead of self called functions
'''

import os
import sys
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

        logger.debug("Ansible scan of: %s", self.machines)
        self.render_inventory()
        command = '/usr/bin/ansible-playbook -i {dir}/inventory.yml {dir}/site.yml --private-key /home/orthos/.ssh/master'.format(dir=Ansible.facts_dir)
        stdout, stderr, returncode = execute(command)
        logger.debug("Calling: %s - %d", command, returncode)
        logger.debug("ansible: %s - %s - %s" % (stdout, stderr, returncode))
        files = self.get_json_filelist()
        missing = list(set(self.machines) - set(files))
        logger.debug("Json result files avail: %s", files)
        for fqdn in files:
            try:
                self.store_machine_info(fqdn)
            except Exception:
                logger.exception("Could not store ansible data of host %s", fqdn)

    def get_json_filelist(self) -> list:
        """
        Returns the list of machines for which json files have been
        created via ansible scan (.json suffix removed)
        """
        res_files = []
        for subdir, dirs, files in os.walk(Ansible.data_dir):
            for jfile in files:
                if jfile.endswith(".json"):
                    logger.debug("Adding: %s - %s", jfile[:-len(".json")], jfile)
                    res_files.append(jfile[:-len(".json")])
        return res_files

    @staticmethod
    def store_machine_info(machine_fqdn: str):

        ans_file = os.path.join(Ansible.data_dir, machine_fqdn + '.json')

        with open(ans_file, 'r') as json_file:
            ansible_machine = json.load(json_file)

        db_machine = Machine.objects.get(fqdn=machine_fqdn)

        Ansible.write_ansible_local(db_machine, ansible_machine)
    
        db_machine.save()
    
    # # prints all non magic attributes of a machine
    # db_machine_attributes = [attribute for attribute in dir(db_machine) if not attribute.startswith('_')]
    # for db_machine_attribute in db_machine_attributes:
    #     try:
    #         attribute_value = getattr(db_machine, db_machine_attribute)
    #         print(f"db_machine.{db_machine_attribute} = {getattr(db_machine, db_machine_attribute)}")
    #     except Exception:
    #         continue
   

    #def get_hardware_information(fqdn):
    @staticmethod
    def write_ansible_local(db_machine, ansible_machine):
        """Retrieve information of the system."""
    
        db_machine.fqdn = ansible_machine.get("fqdn", "")
    
        # db_machine.cpu_physical =  
    
        db_machine.cpu_cores = 5 #ansible_machine.get("processor_cores", 0)
    
        db_machine.cpu_threads = ansible_machine.get("processor_cores", 0) * ansible_machine.get("processor_threads_per_core", 0)
        # db_machine.cpu_model =
        # db_machine.cpu_flags = # --> check if in ansible, else create facts file
        # db_machine.cpu_speed =
        # db_machine.cpu_id =
    
        db_machine.ram_amount = int(ansible_machine.get("memtotal_mb", 0)) * 1024
    
        # db_machine.disk_primary_size = # sectors * sector_size der 1. platte (in bytes). danach hwinfo --disk entfernen.
        # db_machine.disk_type =
    
        db_machine.lsmod = normalize_ascii("".join(ansible_machine.get("ansible_local", {}).get("lsmod", {}).get("noargs", {}).get("stdout", "")))
        db_machine.lspci = normalize_ascii("".join(ansible_machine.get("lspci", {}).get("-vvv -nn", {}).get("stdout", "")))
        last = ansible_machine.get("ansible_local", {}).get("last", {}).get("latest", {}).get("stdout", "")
        db_machine.last = last[0:8] + last[38:49] if len(last) > 49 else ""
        db_machine.hwinfo = normalize_ascii("".join(ansible_machine.get("ansible_local", {}).get("hwinfo", {}).get("full", {}).get("stdout", "")))
        db_machine.dmidecode = normalize_ascii("".join(ansible_machine.get("ansible_local", {}).get("dmidecode", {}).get("noargs", {}).get("stdout", "")))
        db_machine.dmesg = normalize_ascii("".join(ansible_machine.get("ansible_local", {}).get("dmesg", {}).get("-xl", {}).get("stdout", "")))
        db_machine.lsscsi = normalize_ascii("".join(ansible_machine.get("ansible_local", {}).get("lsscsi", {}).get("-s", {}).get("stdout", "")))
        db_machine.lsusb = normalize_ascii("".join(ansible_machine.get("ansible_local", {}).get("lsusb", {}).get("noargs", {}).get("stdout", "")))
        db_machine.ipmi = "IPMI" in db_machine.dmidecode

        try:
            bios_date = ansible_machine.get("bios_date", "")
            if bios_date:
                # Django date fields must be in "%Y-%m-%d" format
                b_date = datetime.strptime(bios_date, "%m/%d/%Y").strftime("%Y-%m-%d")
                logger.warning(b_date)
            else:
                raise ValueError("No bios_date string in %s" % db_machine.fqdn)
            db_machine.bios_date = b_date
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
    
    db_machine.ram_amount =
    db_machine.architecture = ansible_machine.get("architecture")                    
    db_machine.cpu_cores =
    db_machine.efi
    db_machine.cpu_id
    db_machine.cpu_model
 
    attributes where its values probably need to be edited before assigning:
 
    db_machine.bios_version =
    db_machine.disk_primary_size =
    db_machine.disk_type = 
    db_machine.vm_capable = 
    db_machine.cpu_flags = 
    db_machine.cpu_physical =
    db_machine.cpu_physical.cpu_cores =
    db_machine.cpu_physical.cpu_threads =
    db_machine.cpu_physical.cpu_speed = 
     
    attributes where its values may need more complex parsing before assigning, like program outputs:
 
    db_machine.lsmod = 
    db_machine.last = 
    db_machine.efi = 
    db_machine.ipmi =
    db_machine.hwinfo =
    db_machine.dmidecode =
    db_machine.dmesg =
    db_machine.lsscsi =
    db_machine.lsusb =
    db_machine.lspci =
    '''

# call python3 ansible.py for testing
def run(*args):
    machines = [ "trick.arch.suse.de", "ampere3.arch.suse.de" ]
    ansible = Ansible()
    ansible.render_inventory(machines)
    
if __name__ == "__main__":
    run(sys.argv)
