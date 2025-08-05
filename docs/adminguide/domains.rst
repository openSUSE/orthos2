*******
Domains
*******

Concepts
########

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

Domain fields description
#########################

Name (required)
===============

The domain name must be a valid domain, this has to be stored on the DNS and the domain must be valid according to the
valid domain endings configured in Server Configurations (key ``domain.validendings``).

Example: Key: suse.de, suse.cz

Cobbler Server
==============

Responsible Cobbler server.

Cobbler Server Username
=======================

The username to login to Cobbler via XML-RPC.

Example: ``cobbler``

Cobbler Server Password
=======================

The password to login to Cobbler via XML-RPC.

Example: ``cobbler``

TFTP Server
===========

TFTP server from which you are installing your machines. Here, for example, are: Grub2 files, Installation Scripts,
Installation Images, Autoyast files and so on.

Example: music.arch.suse.de

CScreen Server
==============

The serial console server that hosts all serial console.

IPv4 Address
============

The IPv4 network address of the network that is to be managed.

Example: ``192.0.2.0``

IPv6 Address
============

The IPV6 network address of the network that is to be managed.

Example: ``2001:db8::0``

IPv4 subnet mask
================

The IPv4 subnet mask of the network.

IPv6 subnet mask
================

The IPv6 subnet mask of the network.

Enable IPv4 addresses
=====================

If IPv4 addresses should be enabled for the network.

Enable IPv6 addresses
=====================

If IPv6 addresses should be enabled for the network.

Dynamic range v4 start
======================

The start of the range for auto-generated IPv4 addresses that are handed out by Orthos 2.

Dynamic range v4 end
====================

The end of the range for auto-generated IPv4 addresses that are handed out by Orthos 2.

Dynamic range v6 start
======================

The start of the range for auto-generated IPv6 addresses that are handed out by Orthos 2.

Dynamic range v6 end
====================

The end of the range for auto-generated IPv6 addresses that are handed out by Orthos 2.

Setup architectures
===================

Here the list of domains with their corresponding contact e-mails are being listed. If an architecture is not listed,
its machines cannot use the "Setup machine" functionality.
