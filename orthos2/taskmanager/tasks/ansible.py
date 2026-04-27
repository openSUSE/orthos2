"""
This code came from utils/machinechecks "get_hardware_information()" which invoked self made shell scripts.
This function/module will replace "get_hardware_information()" by passing ansible collected data instead of self
called functions.
"""

import glob
import json
import logging
import os
import re
import shutil
import threading
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.template.loader import render_to_string

from orthos2.data.models import Machine
from orthos2.taskmanager.models import Task
from orthos2.utils.misc import execute, normalize_ascii

logger = logging.getLogger("tasks")


class Ansible(Task):

    data_dir = "/run/orthos2/ansible"
    data_dir_lastrun = "/run/orthos2/ansible_lastrun"
    data_dir_archive = "/run/orthos2/ansible_archive"
    facts_dir = "/usr/lib/orthos2/ansible"

    def __init__(self, machines: List[str]) -> None:
        """
        param machines: List of machines (strings) to scan via ansible
        """
        self.machines = machines

        self.thread_id = threading.current_thread().ident
        self.inventory_yml = os.path.join(Ansible.facts_dir, "inventory.yml")
        self.inventory_template = os.path.join(Ansible.facts_dir, "inventory.template")

    def render_inventory(self) -> None:
        """
        Creates an ansible inventory file from the template Ansible.inventory_yml
        and fills it with machines to scan
        """
        rendered = render_to_string(
            self.inventory_template, {"machine_list": self.machines}
        )
        with open(self.inventory_yml, "w") as i_file:
            i_file.write(rendered)

    def execute(self) -> None:
        self.render_inventory()
        command = (
            "/usr/bin/ansible-playbook -i {dir}/inventory.yml {dir}/site.yml".format(
                dir=Ansible.facts_dir
            )
        )
        stdout, stderr, returncode = execute(command)
        logger.debug("Calling: %s - %d", command, returncode)
        logger.debug("ansible: %s - %s - %s", stdout, stderr, returncode)
        files = self.get_json_filelist()
        missing = list(set(self.machines) - set(files))
        if missing:
            logger.warning(
                "Cannot scan machines %s via ansible, missing json file in %s",
                self.machines,
                Ansible.data_dir,
            )
        success: List[str] = []
        fail: List[str] = []
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

    def get_json_filelist(self) -> List[str]:
        """
        Returns the list of machines for which json files have been
        created via ansible scan (.json suffix removed)
        """
        res_files: List[str] = []
        for _subdir, _dirs, files in os.walk(Ansible.data_dir):
            for jfile in files:
                if jfile.endswith(".json"):
                    res_files.append(jfile[: -len(".json")])
        return res_files

    @staticmethod
    def get_ansible_data(
        machine_fqdn: str, try_lastruns: bool = False
    ) -> Optional[Dict[str, Any]]:

        ans_file = os.path.join(Ansible.data_dir, machine_fqdn + ".json")
        if not os.path.isfile(ans_file):
            if not try_lastruns:
                logger.exception("json file %s does not exist", ans_file)
                return None
            else:
                ans_file = os.path.join(
                    Ansible.data_dir_lastrun, machine_fqdn + ".json"
                )
                if not os.path.isfile(ans_file):
                    ans_file = os.path.join(
                        Ansible.data_dir_archive, machine_fqdn + ".json"
                    )
                    if not os.path.isfile(ans_file):
                        logger.exception("json file %s does not exist", ans_file)
                        return None
        try:
            with open(ans_file, "r") as json_file:
                ansible_machine = json.load(json_file)
        except Exception as e:
            logger.exception(
                "Could not load ansible json file %s - %s", ans_file, repr(e)
            )
            return None

        return ansible_machine

    @staticmethod
    def store_machine_info(machine_fqdn: str) -> None:

        ansible_machine = Ansible.get_ansible_data(machine_fqdn)
        if not ansible_machine:
            return
        db_machine = Machine.objects.get(fqdn=machine_fqdn)

        Ansible.write_ansible_local(db_machine, ansible_machine)
        db_machine.save()

    @staticmethod
    def print_machine_info(machine_fqdn: str) -> None:
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
        db_machine_attributes = [
            attribute for attribute in dir(db_machine) if not attribute.startswith("_")
        ]
        for db_machine_attribute in db_machine_attributes:
            try:
                print(
                    f"db_machine.{db_machine_attribute} = {getattr(db_machine, db_machine_attribute)}"
                )
            except Exception:
                continue

    @staticmethod
    def print_ansible_info(machine_fqdn: str) -> None:
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
            print(key, "->", ansible_machine[key])
        return

    # def get_hardware_information(fqdn):
    @staticmethod
    def write_ansible_local(
        db_machine: Machine, ansible_machine: Dict[str, Any]
    ) -> None:
        """
        Write ansible information retrieved from a json file to the system.
        For developing/debugging this interface can directly be use
        (without doing a rescan of the remote machine) via e.g.
        manage runscript store_machine_info --script-args lammermuir.arch.suse.de
        This can be useful if one wants to assign data which was already via ansible
        to the correct database fields here.
        """
        # Amount of real CPU sockets
        db_machine.cpu_physical = ansible_machine.get("processor_count", 1)
        # Amount of all CPU cores (sockets * cores_per_socket)
        db_machine.cpu_cores = (
            ansible_machine.get("processor_cores", 1) * db_machine.cpu_physical
        )
        # Amount of all CPU threads (All CPU cores * threads_per_core)
        db_machine.cpu_threads = db_machine.cpu_cores * ansible_machine.get(
            "processor_threads_per_core", 1
        )

        # CPU model, flags, and ID from custom cpuinfo.fact
        cpuinfo = ansible_machine.get("ansible_local", {}).get("cpuinfo", {})
        db_machine.cpu_model = cpuinfo.get("model_name", "")[:200]
        db_machine.cpu_flags = cpuinfo.get("flags", "")
        db_machine.cpu_id = cpuinfo.get("cpuid", "")[:200]
        # CPU speed from dmidecode "Max Speed" field (stored as GHz)
        cpu_speed_ghz = Decimal(0)
        if db_machine.dmidecode:
            # Search for "Max Speed" in dmidecode output
            for line in db_machine.dmidecode.split("\n"):
                if "Max Speed" in line and ":" in line:
                    # Extract value after ":"
                    speed_str = line.split(":", 1)[1].strip()
                    # Parse number and unit (e.g., "3600 MHz" or "3.6 GHz")
                    match = re.search(r"([\d.]+)\s*(MHz|GHz)", speed_str, re.IGNORECASE)
                    if match:
                        speed_value = Decimal(match.group(1))
                        unit = match.group(2).upper()
                        if unit == "MHZ":
                            # Convert MHz to GHz
                            cpu_speed_ghz = speed_value / 1000
                        elif unit == "GHZ":
                            cpu_speed_ghz = speed_value
                    break
        db_machine.cpu_speed = cpu_speed_ghz

        db_machine.ram_amount = int(ansible_machine.get("memtotal_mb", 0))

        # Disk primary size and type from ansible_devices
        devices = ansible_machine.get("devices", {})
        # Filter for block devices (exclude loop, ram, sr/cdrom devices)
        block_devices = {
            k: v
            for k, v in devices.items()
            if not k.startswith(("loop", "ram", "sr", "dm-")) and v.get("size")
        }
        if block_devices:
            # Get first device alphabetically (sda, vda, nvme0n1, etc.)
            first_device = sorted(block_devices.keys())[0]
            device_info = block_devices[first_device]

            # Parse disk size - can be "476.94 GB", "500107862016" (bytes), or other formats
            size_str = device_info.get("size", "0")
            size_gb = 0
            # Try to parse size in various formats
            if "GB" in size_str or "GiB" in size_str:
                # Extract number from "476.94 GB" format
                match = re.search(r"([\d.]+)\s*G[iB]", size_str)
                if match:
                    size_gb = int(float(match.group(1)))
            elif "TB" in size_str or "TiB" in size_str:
                # Extract number from TB format and convert to GB
                match = re.search(r"([\d.]+)\s*T[iB]", size_str)
                if match:
                    size_gb = int(float(match.group(1)) * 1024)
            elif size_str.replace(".", "").isdigit():
                # Assume it's bytes, convert to GB
                size_gb = int(float(size_str) / (1024**3))

            db_machine.disk_primary_size = size_gb

            # Determine disk type (NVMe, SSD, HDD)
            rotational = device_info.get("rotational", "1")
            if first_device.startswith("nvme"):
                db_machine.disk_type = "NVMe"
            elif rotational == "0":
                db_machine.disk_type = "SSD"
            else:
                db_machine.disk_type = "HDD"
        else:
            db_machine.disk_primary_size = None
            db_machine.disk_type = ""

        # Populate discovered kernel options from cmdline fact
        k_opts = ansible_machine.get("cmdline", {})
        if k_opts and isinstance(k_opts, dict):
            # Format as space-separated key=value pairs, handle flags without values
            formatted_opts = []
            for key, value in k_opts.items():
                if value:  # key=value format
                    formatted_opts.append(f"{key}={value}")
                else:  # flag without value (e.g., "quiet", "ro")
                    formatted_opts.append(key)
            db_machine.kernel_options_discovered = " ".join(formatted_opts)
        else:
            db_machine.kernel_options_discovered = ""

        db_machine.lsmod = normalize_ascii(
            "".join(
                ansible_machine.get("ansible_local", {})
                .get("lsmod", {})
                .get("noargs", {})
                .get("stdout", "")
            )
        )
        db_machine.lspci = normalize_ascii(
            "".join(
                ansible_machine.get("ansible_local", {})
                .get("lspci", {})
                .get("-vvv -nn", {})
                .get("stdout", "")
            )
        )
        last = (
            ansible_machine.get("ansible_local", {})
            .get("last", {})
            .get("latest", {})
            .get("stdout", "")
        )
        db_machine.last = last[0:8] + last[38:49] if len(last) > 49 else ""
        db_machine.hwinfo = normalize_ascii(
            "".join(
                ansible_machine.get("ansible_local", {})
                .get("hwinfo", {})
                .get("full", {})
                .get("stdout", "")
            )
        )
        db_machine.dmidecode = normalize_ascii(
            "".join(
                ansible_machine.get("ansible_local", {})
                .get("dmidecode", {})
                .get("noargs", {})
                .get("stdout", "")
            )
        )
        db_machine.dmesg = normalize_ascii(
            "".join(
                ansible_machine.get("ansible_local", {})
                .get("dmesg", {})
                .get("-xl", {})
                .get("stdout", "")
            )
        )
        db_machine.lsscsi = normalize_ascii(
            "".join(
                ansible_machine.get("ansible_local", {})
                .get("lsscsi", {})
                .get("-s", {})
                .get("stdout", "")
            )
        )
        db_machine.lsusb = normalize_ascii(
            "".join(
                ansible_machine.get("ansible_local", {})
                .get("lsusb", {})
                .get("noargs", {})
                .get("stdout", "")
            )
        )
        db_machine.ipmi = "IPMI" in db_machine.dmidecode

        try:
            bios_date = ansible_machine.get("bios_date", None)
            if bios_date == "NA":
                bios_date = None
            if bios_date:
                # Django date fields must be in "%Y-%m-%d" format
                db_machine.bios_date = datetime.strptime(  # type: ignore
                    bios_date, "%m/%d/%Y"
                ).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            logger.exception("Could not parse bios date [%s]", db_machine.fqdn)

        db_machine.bios_version = ansible_machine.get("bios_version", "")

        # EFI detection - check if /boot/efi is mounted
        mounts = ansible_machine.get("mounts", [])
        db_machine.efi = any(mount.get("mount") == "/boot/efi" for mount in mounts)

        # VM capable - check CPU flags for virtualization extensions (vmx/svm)
        cpu_flags_lower = db_machine.cpu_flags.lower()
        db_machine.vm_capable = "vmx" in cpu_flags_lower or "svm" in cpu_flags_lower
