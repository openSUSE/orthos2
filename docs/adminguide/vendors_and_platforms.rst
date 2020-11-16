*********************
Vendors and Platforms
*********************

Under Vendors you can enter the machine manufacturer, this serves together with the platforms to recognize a machine, or
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

Example: 4HE Quad 940 Socket

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
