*************
Architectures
*************

Concepts
########

Machine architectures can be set up, the most common ones are already preconfigured. Machine objects have an
architecture that can then be mapped to the machine.

.. code-block::

      -----------
      | Machine |
      -----------
           |
           |
    ----------------
    | Architecture |
    ----------------

Architecture fields description
###############################

Name (required)
===============

Name of the architecture.

Example: s390x, x86_64, ppc64le etc.

DHCP filename
=============

Path to the boot files on the TFTP server.

Contact email
=============

Email address to the person who is the contact person for an architecture.

Default profile
===============

The name of the Cobbler profile used as the default installation choice for machines of this architecture when
using the "Setup Machine" action.
