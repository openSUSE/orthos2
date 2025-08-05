*******************
Serial Console Type
*******************

Concepts
########

Here you can set up the different ways to access a serial console. The best known ones like IPMI, ILO2, Telnet, libvirt
etc. are already predefined. The serial console type can then be converted into a machine object under: Machine >
SERIAL CONSOLE > Type can be set.

.. code-block::

    -----------     -----------------------
    | Machine |-----| Serial Console Type |
    -----------     -----------------------

In the following are the fields for the Serial Console Type with explanations.

Serial Console Type fields description
######################################

Name (required)
===============

Name of the Serial Console Type.

Command
=======

Command which is required to access the serial console. In Orthos you use variables/objects to create a serial console
type. These are written in double curly brackets ``{{ ... }}``.

Example: ``virsh -c lxc+ssh://root@{{ machine.hypervisor.fqdn }}/system console {{ machine.hostname }}``

The objects are taken from the machine object or the respective entries at the machine. Such as, for example.

- Hostname = machine.Hostname
- BMC FQDN = machine.bmc.fqdn
- Hypervisor FQDN = machine.hypervisor.fqdn
- Console Server FQDN = console_server.fqdn
- IPMI User = ipmi.user
- IPMI Password = ipmi.password

Comment
=======

Additional information to the Serial Console Type.

