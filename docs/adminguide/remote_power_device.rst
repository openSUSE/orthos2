********************
Remote Power Devices
********************

Concepts
########

See "Remote Power Type" concepts. In short this maps a fence agent to a target "Machine".

Remote Power Device fields description
######################################

FQDN (required)
===============

The FQDN that should be choosen for the power device.

MAC (required)
==============

The MAC address of the device.

Username (required)
===================

The username to login to the remote power device.

Password (required)
===================

The password to login to the remote power device.

Fence Agent (required)
======================

The fence agent used. This is a choice field that shows all Orthos 2 Remote Power Types that are available for the type
"rpower".

URL
===

URL of the Webinterface to configure this Power Device. Power devices should be in a separate management network only
reachable via the cobbler server. In this case the Webinterface might be port forwarded, also check Documentation.
