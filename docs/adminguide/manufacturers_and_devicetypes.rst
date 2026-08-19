******************************
Manufacturers and Device Types
******************************

Concepts
########

Under Manufacturers you can enter the machine manufacturer, This serves together with the device types to recognize a machine or
machines of the same type. Most manufacturers are already stored in the Orthos system. With device types you can set the
machine family name (unit name). It goes hand in hand with the manufacturer, the device type name is determined by the manufacturer.

.. code-block::

    ----------------
    | Manufacturer |
    ----------------
          |
          |
    -------------
    | DeviceType |
    -------------
          |
          |
    -------------     -----------
    | Enclosure |-----| Machine |
    -------------     -----------

Manufacturer fields description
###############################

Name (required)
===============

Name of the manufacturer.

Example: AMD, IBM, Raritan, Dell, Intel, SGI etc.

Device Type fields description
###############################

Name (required)
===============

Name of the device type specified by the manufacturer.
On x86 systems you often get an idea via dmidecode command, e.g.:
`
dmidecode -s system-product-name
Latitude E7470
`

But this info is often empty or wrong, especially on early developement machines.
Therefore it has to be filled manually.
It should be a meaningful name, by which people who are familiar with products
of the manufacturer have an idea what kind of machine this is (how old, features, etc.).

Manufacturer (required)
=======================

Here a manufacturer is specified and the connection between device type and manufacturer created.

Example: AMD, IBM, Raritan, Dell, Intel, SGI etc.

Cartridge/Blade
===============

If the device type is a cartridge/blade system, a hook must be set here.

Description
===========

More information about the device type.
