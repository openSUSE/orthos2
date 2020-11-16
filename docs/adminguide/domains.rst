*******
Domains
*******

Here you can set up a domain under Orthos, a domain must also be set up on a DNS server. That Orthos can install
machines, it is absolutely necessary to specify the DHCP server, TFTP server and the architectures. Orthos is able to
write the DHCP file for these domains.The FQDN of a machine object is bound to a domain.

.. code-block::

                   -----------
                   | Machine |
                   |         |
    ----------     -----------
    | Domain |-----|  FQDN   |
    ----------     -----------

Domain fields description:

Name (required)
###############

The domain name must be a valid domain, this has to be stored on the DNS and the domain must be valid according to the valid domain endings configured in Server Configurations (key domain.validendings).

Example: Key: suse.de, suse.cz

DHCP Server
###########

Responsible DHCP server for the domain.

Example: music.arch.suse.de

TFTP Server
###########

TFTP server from which you are installing your machines. Here, for example, are: Grub2 files, Installation Scripts, Installation Images, Autoyast files and so on.

Example: music.arch.suse.de

Setup architectures
###################

A domain can contain several architectures, for these a corresponding DHCP file is then written and the appropriate installation files and scripts are offered.

Example: x86_64, ppc64le, s390x

Setup machine groups
####################

Here it is possible to add machine groups.

