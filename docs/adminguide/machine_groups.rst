**************
Machine Groups
**************

In Orthos it is possible to group machines. Users can be assigned to one or more machine groups. Only users assigned to
a group of machines can reserve and work with this set of machines. It is possible to assign different administrative
rights.

.. code-block::

    --------------------
    | Privileged Users |
    --------------------
    |      Users       |
    --------------------     -----------
             |               | Machine |
             |              /-----------
     -----------------     /
     | Machine Group |----<
     -----------------     \
                            \-----------
                             | Machine |
                             -----------

Machine fields description
##########################

Name (required)
===============

Name of the machine group.

Comment
=======

Comment about the machine group.

DHCP filename
=============

Path to the boot files on the TFTP server.

Write DHCPv4
============

Enable/disable writing a DHCPv4 file for this machine group.

Write DHCPv6
============

Enable/disable writing a DHCPv6 file for this machine group.

Use machines architecture for setup
===================================

It is possible to set the setup settings of the associated machine architecture for the machine group.

USER
====

Add/delete users to machine group and assign administrative rights.
