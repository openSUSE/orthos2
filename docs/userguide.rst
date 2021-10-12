**********
User Guide
**********

Describes how to use Orthos as a user, how to find, save and install machines for your purposes with the help of Web
GUI and the Command Line Interface (CLI).

.. contents::
    :local:

Introduction
############

Orthos is the machine administration tool of the development network in the ARCH team at SUSE. It is used for following
tasks:

- locating a machine,
- getting the state of the machine,
- overview about the hardware,
- overview about the installed software (installations),
- reservation of the machines,
- generating the DHCP configuration,
- reboot the machines remotely and
- managing remote consoles.

This document describes the usage. For implementation specific notes, please refer to the “Developer’s Guide”. However,
sometimes this document describes some aspects of the implementation simply to let the user better understand why things
work as they do. All users of Orthos have a very technical background.


Architecture
############

.. image:: img/userguide/00_architecture.png
  :alt: Orthos2 High-Level Architecture

Image Overall Architecture shows the overall architecture. All data is kept in the database. The Orthos Server is the
central component of Orthos. It has the following tasks:

- gathering machine data,
- communicating with the clients,
- executing jobs such as rebooting or installating the machine or syncing some files.

There are two clients: The command line interface and the web interface. While the web interface is able to deal with
basic tasks such as getting a machine overview and reserving a machine, the CLI is able to deal with more complicated
tasks such as executing queries and even edit the data.

Web Client
##########

Via the link to your webserver domain it is possible to use the Orthos Web Client. The Web Client is mostly
self-explanatory, so only the most important things are explained. You can log in via the web client with an LDAP user
account. This is a normal user and has no administrative rights.This means that it is not possible to create and delete machine objects
yourself and so on. With this account it is possible to use machines.

You can:

- Search for suitable machines
- Reserve machines for you
- Install the machines you need with SLES, SLED, openSUSE Leap and openSUSE tumbleweed,...
- Perform various machine checks
- Get information about machines and test their accessibility
- Add annotations for each machine (Machine Features, Glitches, Hardware Upgrades, Bios Updates, etc.)
- Report Problems for each machine
- Get an overview of the reservation history

If administrative rights are required, they must be set up by an Orthos administrator. Below a screenshot of the login
page.

.. image:: img/userguide/01_login_screen.jpg
  :alt: Orthos2 Login Screen

Landing Page
============

After logging in you will be redirected to the Orthos landing page. Here you will find a direct overview of all machines
that are available in Orthos.

.. image:: img/userguide/02_landingpage.jpg
  :alt: Orthos2 Landing Page

Here different possibilities are available to get to machines or to get an entire machine status.

.. image:: img/userguide/03_top_menu_overviews.jpg
  :alt: Orthos2 Top Menu Overview

- All Machines: Overview of all machines that are available in Orthos.
- Free Machines: Overview of all machines that are available in Orthos.
- My Machines: Overview of all Orthos machines reserved under your name.
- Virtual Machines: Overview of all virtual machines. (Host/Gast).
- Advanced Search: Advanced machine search.
- Statistics: Statistics about the machines located in Orthos.

.. image:: img/userguide/04_arch_quickfilter.jpg
  :alt: Orthos2 Architecture Quickfilter

- x86_64, unspecified, embedded, ia64, s390x, ppc64le etc: Sorting by architecture
- Ping, SSH and Login: Sort by availability status.
- All Network Domains: Sort by network domain.
- All Machine Groups: Overview and sorting of machines in the respective machine group.


Machine Page
============

Each machine (machine object) has its own page here you have the possibility to get more detailed information about the
machine, to request the status of a machine, to have machines scanned, to install the machine with a new OS, to open
error tickets and to write annotations to the machines.

.. image:: img/userguide/05_machine_page.jpg
  :alt: Orthos2 Machine Overview Page

Machine Scans, Infos, Actions and Annotations

.. image:: img/userguide/06_machine_infos.jpg
  :alt: Orthos2 Machine Details Tabs

- Overview: The most important information about a machine, information about the status, possibility to scan the
  machine, to reinstall, to report errors and to write annotations.
- CPU, Network, Installation, PCI, USB, SCSI, Miscellaneous and Reservation History: Detailed information on the
  Subitems.

.. image:: img/userguide/07_machine_status.jpg
  :alt: Orthos2 Machine Overview - Crop on Network Status

- IPv4 / IPv6: Ping status of a machine IPv4 and IPv6.
- SSH: Orthos tries if it would be possible to establish an SSH connection.
- Login: If a connection with SSH is possible, Orthos tries if a login is also possible.

The scan behaviour of Orthos can be defined by an administrator for the respective machine object.

.. image:: img/userguide/08_machine_annotations.jpg
  :alt: Orthos2 Machine Overview - Crop on Annotations

Additional machine information should be entered here. For example, upgrades, hardware configuration changes, etc.

.. image:: img/userguide/09_machine_actions.jpg
  :alt: Orthos2 Machine Overview - Crop on Actions

- Reserve Machines: Here it is possible to reserve a machine under your name. In general, make sure that machines are only reserved for as long as you actually need them. A maximum of 90 days is planned. Please remember that other users may also need the machine. If you need a machine for a longer period of time, only an Orthos administrator can make reservations under your name for longer time periods, up to infinite for constant machine assignment.
- Rescan Status: Rescan the status information of a machine.
- Rescan All: Rescan all information of a machine.
- Rescan Installations: Resacan the installation status of a machine.
- Rescan Network Interfaces: Rescan the machine network interfaces.
- Setup Machine: Here you can install your machine according to your needs. You have the possibility to install SLES, SLED, Opensuse Leap, Opensuse and Tumbleweed. During the installation you have several options: install, install ssh install ssh auto, install auto etc.
- Report Problem: If you unexpectedly encounter a problem with the machine, you can create a support ticket here.

.. image:: img/userguide/10_machine_release.jpg
  :alt: Orthos2 Machine Overview - Crop on Release & Extend Reservation

- Release Machine: This field is only for machines that are reserved under your name. Here you have the possibility to release the machine for other users.

Virtual Machines
================

In Orthos it is possible that you work with virtual machines. You can work with a virtual machine as well as with a
bare metal machine. You can use the Power Cycle and access the console.

.. image:: img/userguide/11_machine_virtual.jpg
  :alt: Orthos2 Virtual Machine Overview

Under Virtual Machine select a VM host and click on the plus (+) to create a VM guest.

.. image:: img/userguide/12_machine_virtual_gast.jpg
  :alt: Orthos2 Virtual Machine Details

After Add Virtual Machines the VM host is created and made available under the My Machines
