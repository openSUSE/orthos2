*********************
Vendors and Platforms
*********************

Concepts
########

Under Vendors you can enter the machine manufacturer, This serves together with the platforms to recognize a machine or
machines of the same type. Most manufacturers are already stored in the Orthos system. With platforms you can set the
machine family name (unit name). It goes hand in hand with the vendor, the platform name is determined by the vendor.

.. code-block::

    -------------
    |  Vendor   |
    -------------
         |
         |
    -------------
    | Platform  |
    -------------
          |
          |
    -------------     -----------
    | Enclosure |-----| Machine |
    -------------     -----------

Vendor fields description
#########################

Name (required)
===============

Name of the vendor.

Example: AMD, IBM, Raritan, Dell, Intel, SGI etc.

Platform fields description
###########################

Name (required)
===============

Name of the platform specified by the manufacturer.
On x86 systems you often get an idea via dmidecode command, e.g.:
`
dmidecode -s system-product-name
Latitude E7470
`

But this info is often empty or wrong, especially on early developement machines.
Therefore it has to be filled manually.
It should be a meaningful name, by which people who are familiar with products
of the vendor have an idea what kind of machine this is (how old, features, etc.).

Vendor (required)
=================

Here a vendor is specified and the connection between platform and vendor created.

Example: AMD, IBM, Raritan, Dell, Intel, SGI etc.

Cartridge/Blade
===============

If the platform is a cartridge/blade system, a hook must be set here.

Description
===========

More information about the platform.
