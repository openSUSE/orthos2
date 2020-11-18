.. _`machines`:

********
Machines
********

Machines are the elementary objects in Orthos. They are entities like Servers, Desktop PCs, Virtual Machines (VM), Baseboard Management Controller (BMC), Remote Power devices etc. Machines can be administrative in order to serve as serial console, DHCP server etc. Administrative machines typically are productive and must not be touched. Users are able to reserve machine objects. The following figure shows the machine object organization in general:

.. code-block::

    -------------
    | Platform  |
    -------------
          |
    -------------    -----------------
    | Enclosure |    |  RemotePower  |
    -------------    -----------------
          |         /
    -------------  / -----------------
    |  Machine  |----| SerialConsole |
    -------------    -----------------




Machine fields description
##########################

FQDN (required)
===============

The fully qualified domain name must be DNS resolvable by the Orthos server. The domain must be valid according to the valid domain endings configured in Server Configurations (key domain.validendings).

Example: bach.arch.suse.de

Enclosure
=========

The corresponding enclosure object. A enclosure object represents the phyiscal chassis of a machine. If no enclosure object is selected, a new object will be created (using the machines hostname).

Example: bach

MAC address (required)
======================

Media Access Control address (MAC) of the primary network interface. This address is used for e.g. DHCP configuration.

Example: 3C:A8:2A:10:74:C3

Architecture (required)
=======================

The architecture of the machine. The architecture should be equal to uname -m output of the Linux system running in the machine-to-be.

Example: x86_64

System (required)
=================

The type of system of the machine.

Example: VM, BMC, BareMetal, LPAR, Desctop, RemotePower etc.

Serial number/Product code/Platform
===================================

Specified by the manufacturer. Mostly there is a sticker with the serial number and the product code on the machine's chassis, which has to be entered here.

Example: Serial number: GPKLDV6120104 / Product code: MAKL1K1PFB / Platform: Knights Landing

Kernel option
=============

Kernel options are passed via boot loader to the kernel. New values can be set here, or appended with a plus (+). You can find explanations of the kernel options in the GRUB 2 documentation.

Administrative machine
======================

Important and productive administration servers inside the orthos network environment like DHCP, remote power switches, etc. "Do not touch"!

Example: RemotePower, SerialConsole, DHCP Server etc.

NDA Hardware
============

It marks machines from the Non-disclosure Agreement (NDA) program. Do not publish any details of these machines! If you exchange info like lspci or whatever
hardware specifics, make sure that the bug you post this info in is marked private and people are aware of the sensitivity of the data you post/send.

Active
======

Machine is active and can be used from everybody. If deactivated (adminstrator rights needed), the machine is hidden for ordinary users.

Dedicated VM host
=================

It marks whether the machine can be used as VM host in Orthos. VM guests can then be created on the machine and again managed by Orthos.

Delete automatically
====================

Determine whether the VM Guest is deleted after the end of the reservation.

Max VMs
=======

Maximum number of possible guest systems on the VM host. The number of VM guests depends on the hardware properties of the host.

Virtualization API
==================

The solution that provides virtualization on the host system.

Example: libvirt etc.

Check connectivity
==================

Determined whether and how Orthos checks the accessibility of the machine.

Example: Ping, SSH or SSH with login

Collect system information
==========================

Orthos can scan the machines and make them available to the system for information.

Example: dmesg, dmicode etc.

DHCPv4
======

How to handle the DHCPv4 server v4.

Example: exclude, write DHCPv4 record or ignore DHCPv4 request

DHCPv6
======

How to handle the DHCPv6 server v6.

Example: exclude, write DHCPv6 record or ignore DHCPv6 request

DHCP filename
=============

Here you can store a machine-specific boot file for PXE and UEFI. See also the GRUB2 documentation.

SERIAL CONSOLE description
##########################

Type
====

Access type to the serial console of the machine.

Example: Telnet, IPMI, free command etc

CScreen server
==============

A cscreen server is a server on which the cscreen service is installed and entered.

Example: sconsole1.arch.suse.de

Baud rate
=========

Serial console transfer rate.

Example: 115200, 57600, 9600

Kernel device
=============

Kernel device on which the kernel outputs the serial signal.

Example: 0, 1 etc.

Management BMC
==============

Here a BMC for serial over lan can be selected, it must be created similar to a machine.

Example: bahama-sp.arch.suse.de

Dedicated console server
========================

A dedicated console server is an embedded device which is only for merging multiple consoles and then deploying. Access is via telnet. Access to the console runs via the CScreen srever.

Example: sconsole3.arch.suse.de

Device
======

Kernel device through which the output for the serial console runs.

Example: ttyS0, ttyS1 etc.

Port
====

Network port for accessing the serial console.

Command
=======

A free command can be entered here.

Example: telnet sconsole3.arch.suse.de 2008

REMOTE POWER description
########################

Type
====

Access type to the RemotePower console of the machine.

Example: Telnet, IPMI etc.

Management BMC
==============

BMC can be selected, it must be created similar to a machine.

Example: bahama-sp.arch.suse.de

Remote power device
===================

Here a RemotePower device can be selected, it must be created similar to a machine.

Example: rpower1.arch.suse.de

Port
====

Network port for accessing the RemotePower.

Comment
=======

Comment indicating the remote power device.

Delete a machine
################

To delete a machine, choose from the machine list and press 'Delete' at the bottom of the machine view. All related
information that is also deleted together with the machine object is displayed. Press ``Yes`` to confirm. For
administrative reasons, a copy of each deleted machine object is stored in the form of a file. The format (JSON, Yaml)
as well as the target directory can be set via the server configuration.

Further configuration information can be found in the :ref:`admin-guide` (``serialization.*``).

.. note::

    When running in production mode, make sure the target directory (``serialization.output.directory``) can be written
    by the webserver user.
