********************
Server Configuration
********************

settings.py
###########

The list of settings below can be modified at runtime on the host that hosts the application.
For the settings to take effect, a restart of both Orthos 2 and the Orthos 2 Taskmanager is required.

All defaults are set inside the ``settings.py`` file which is contained in the Python package.
To override them please use the file ``/etc/orthos2/settings``. The settings files follow the Python 3 syntax.

NETBOX_URL
==========

URL in the format of ``<protocol>://<fqdn>:<port>``. Specifies the NetBox instance used to retrieve data from.

Environment Variable: ``ORTHOS_NETBOX_URL``

Default: ``""`` (empty string)

Example: ``https://netbox.example.org``

NETBOX_TOKEN
============

NetBox API Token to retrieve data from the instance specified at ``NETBOX_URL``.

Environment Variable: ``ORTHOS_NETBOX_TOKEN``

Default: ``""`` (emtpy string)

Example: ``1111111111aaaaaaaa22222222bbbbbbbb333333``

ServerConfig
############

The list of settings below can be modified at runtime in the Django Admin Interface.

``domain.validendings``
=======================

List of valid network domain endings. All FQDN's must match at least one of these.
Multiple endings can be separated by a comma.

Leave empty if all domains should be accepted.

Default: ``example.de, example.com``

Example: ``example.de, example.com, example.bayern``

``mail.from.address``
=====================

Sender field of the emails sent by Orthos.

Default: ``orthos-noreply@domain.de``

``mail.smtprelay.fqdn``
=======================

The SMTP server that is used to send mails. That should be a company-internal server.

Default: ``relay.mail-server.de``

``mail.subject.prefix``
=======================

Subject prefix of the emails sent by Orthos. Each mail gets the prefix before the subject itself (e.g.:
``[ORTHOS] Orthos password restored``).

A whitespace after the prefix is recommended.

Default: ``[ORTHOS]<whitespace>``

``orthos.api.welcomemessage``
=============================

Orthos can show you a welcome message, this can be set here.

Default: blank

``orthos.bugreport.url``
========================

The path to the online repo is set here. If errors occur in the Orthos code, they can be reported there.

Default: https://gitlab.suse.de/orthos-maintainers/orthos2/issues

``orthos.cli.url``
==================

The path to the Orthos command line interface.

Default: https://build.suse.de/package/show/Devel:Archteam:Orthos/orthos-cli

``orthos.configuration.inline.begin``
=====================================

It marks the beginning of a code inserted from Orthos configuration into a configuration files.

Example: = — BEGIN ORTHOS SECTION --

``orthos.configuration.inline.end``
===================================

It marks the ending of a code inserted from Orthos configuration into a configuration files.

Example: = — END ORTHOS SECTION --

``orthos.debug.dhcp.write``
===========================

Here the writing of the DHCP configuration can be activated or deactivated.

``orthos.debug.mail.send``
==========================

Here you can activate or deactivate the writing of Orthos Info E-Mails.

``orthos.debug.motd.write``
===========================

Here you can activate or deactivate that Orthos the motto of the day when installing a machine.

``orthos.debug.serialconsole.write``
====================================

Here the writing of a cscsreen configuration file on the screen server can be activated or deactivated via Orthos.

``orthos.debug.setup.execute``
==============================

Here you can activate or deactivate the writing of the machine installation files via Orthos.

``orthos.documentation.url``
============================

The path to the Orthos documentation.

Default: https://gitlab.suse.de/orthos-maintainers/orthos2/tree/development/docs

``orthos.web.welcomemessage``
=============================

Here you can enter the Orthos welcome message.

Default: blank

``racktables.url.query``
########################

Orthos retrieves the location of a machine via Racktables. It is important to have at least set orthos_id#{{ id }} at the end of the call, only then can Racktable find the appropriate machine.

Default: ``https://orthos.arch.suse.de/cgi-bin/get_location_from_racktables.pl?orthos_id#{{ id }}``

``remotepower.default.password``
================================

Default password for remote power access.

``remotepower.default.username``
================================

Default user for remote power access.

``remotepower.dominionpx.password``
===================================

Password for remote Power Distribution Unit(Dominion PX) access.

Default: xxxxxxx

``remotepower.dominionpx.username.``
====================================

User for remote Power Distribution Unit(Dominion PX) access.

Default: orthos

``remotepower.ipmi.command``
============================

Path and command to power cycle over baseboard management controller (ipmitool).

Default: ``/usr/bin/ipmitool -I lanplus -H {{ machine.bmc.fqdn }} -U {{ ipmi.user }} -P {{ ipmi.password }} power {{ action }}``

``remotepower.ipmi.password``
=============================

Password for remote power access over baseboard management controller.

Default: xxxxxxx

``remotepower.ipmi.username``
=============================

User for remote power access over baseboard management controller.

Default: oroot

``remotepower.sentry.password``
===============================

Password for remote Remote Power Manager(sentry) access.

Default: xxxxxxx

``remotepower.sentry.username``
===============================

User for remote Remote Power Manager(sentry) access.

Default: orthos

``serialconsole.ipmi.password``
===============================

Password for serial over LAN(SOL) over the baseboard management controller.

Default: xxxxxxx

``serialconsole.ipmi.username``
===============================

User for serial over LAN(SOL) over the baseboard management controller.

Default: oroot

``serialization.output.directory``
==================================

Local directory where the machine object copies are stored after deleting a machine
(see [Machines](./adminguide/machine.md) for more information).

Default: ``/tmp``

Example: ``/usr/share/grave``

``serialization.output.format``
===============================

Data format for the machine object copies after deleting a machine. Valid formats
are ``json`` and ``yaml`` (see :ref:`machines` for more information).

Default: ``json``

Example: ``yaml``

``setup.execute.command``
=========================

Here you can store a script that executes Orthos during installation.

Example: /srv/tftpboot/grub2/scripts/setup.py --mac {{ machine.mac_address }} --fqdn {{ machine.fqdn }} --arch {{ machine.architecture.name }} --default {{ choice }} --kernel-options "{{ machine.kernel_options }}" {% if machine.serialconsole %}--serial-console true --serial-baud {{ machine.serialconsole.baud_rate }} --serial-line {{ machine.serialconsole.kernel_device }}{% else %}--serial-console false{% endif %}

``ssh.keys.paths``
==================

File path(s) to private SSH keys. Multiple paths can be separated by a comma.
In production mode (running e.g on Apache webserver), absolute paths should be used.
Each SSH connection tries all keys until one of them matches.

Default: ``./keys/orthos2-master-test``

Example: ``/root/.ssh/id_rsa_cobbler_server, /root/.ssh/id_rsa_sconsole``

``ssh.scripts.local.directory``
===============================

Local directory holding scripts determined for remote execution (e.g. for machine checks).

Default: ``./scripts``

``ssh.scripts.remote.directory``
================================

Remote directory where scripts get copied before they get run on the remote system.

Default: ``/tmp/orthos-scripts``

``ssh.timeout.seconds``
=======================

Set the SSH connecting timeout (in seconds).

Default: ``10``

``tasks.daily.executiontime``
=============================

Time at which the daily tasks are started. Must be in 24h format.

Default: ``00:00``

``virtualization.libvirt.images.directory``
===========================================

Here stores Orthos the images for the virtual machines.

Default: /mounts/users-space/archteam/orthos-vm-images

``virtualization.libvirt.ovmf.path``
====================================

Here is the path for the KVM Support UEFI Binary defined.

Default: usr/share/qemu/ovmf-x86_64-opensuse.bin

``websocket.cscreen.command``
=============================

Local command which gets executed when a serial console gets requested. The service appends the hostname to the command
(e.g. ``/usr/bin/screen host``). The command can be anything returning a terminal (see :ref:`websockets` for more
information).


Default: ``/usr/bin/screen``

``websocket.port``
==================

The port on which the WebSocket service is listening (see :ref:`websockets`) for more information).

Default: ``8010``
