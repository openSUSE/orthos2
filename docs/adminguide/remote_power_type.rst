******************
Remote Power Types
******************

Concepts
########

Remote Power Types represent a fence agent on the Cobbler end. They are responsible for making power operations possible
inside Orthos for a certain machine. A remote Power Type is connected to one of the three available options to a given
machine.

.. code-block::

                                    +-----+                                    
                                    |     |                                    
                           +------->| BMC +------------------------------+     
                           |        |     |                              |     
                           |        +-----+                              v     
    +-------------------+  |        +---------------------+         +---------+
    |                   +--+        |                     |         |         |
    | Remote Power Type +---------->| Remote Power Device +-------->| Machine |
    |                   +--+        |                     |         |         |
    +-------------------+  |        +---------------------+         +---------+
                           |        +--------------+                     ^     
                           |        |              |                     |     
                           +------->| Remote Power +---------------------+     
                                    |              |                           
                                    +--------------+                           


Remote Power Type fields description
####################################

Remote Power Type (required)
============================

The name of the fence agent without the ``fence_`` prefix.

Device
======

The type of fence agent this is. Must be one of "Remote Power Device", "BMC" or "Hypervisor".

Username
========

The default username for the remote power type.

Password
========

The default password for the remote power type.

Identity File
=============

The identity file in case a key is needed to connect to the managed device. This field is translated into a filepath by
the fence agent. As such locations given here must match the path on the Cobbler server.

Supported Architectures
=======================

If none is given, the remote power type is available to all architectures. Select one or more in case this should be
limited to a set of architectures.

Supported Systems
=================

If none is given, the remote power type is available to all systems. Select one or more in case this should be
limited to a set of systems.

Use Port
========

Wether to use the additional port, instead of the standard hostname. This is useful for remotely switchable PDUs.

Use Hostname as Port
====================

Wether to use the additional port and use the Machine hostname instead of the port integer. This is useful for systems
that identify the target system by name.
