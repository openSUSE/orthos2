**********************
Systems and Enclosures
**********************

Systems
#######

Systems are assigned to the machines accordingly, here the type of machine is determined. Most known systems are already stored in Orthos.

.. code-block::

    -------------
    | Enclosure |
    -------------
          |
          |
    -------------     ------------
    |  Machine  |-----|  System  |
    -------------     ------------

System fields description:

Name (required)
===============

Exact name of the system.

Example: BMC, Desktop, LPAR PowerPC etc.

Virtual
=======

Use this if the system a virtual system (VM Gast).

Administrative
==============

Machines that are declared as administrative are machines that belong to the Orthos system and network management. These machines cannot be reserved by the user.

Example: RemotePower

Enclosures
##########

Under Enclosures the case (unit) is defined. A parent name for a unit with several devices can be defined. Several machines can then be assigned to the enclosure. If you create a machine object and you do not specify an enclosure, the name of the enclosure is formed from the FQDN of the machine.

.. code-block::

    -------------
    | Platform  |
    -------------
          |
          |
    -------------     -----------
    | Enclosure |-----| Machine |
    -------------     -----------

System fields description:

Name (required)
===============

Name of the Enclosure.

Platform
========

Here the machine platform is specified, this usually comes via the vendor.

Description
===========

Since Enclosure is the generic term of a complete system, this should be as precise as possible.
