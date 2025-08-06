**************************************
Installation/Setup (Production system)
**************************************

Install the main server
#######################

1. Install the orthos2 package:
    .. code-block::

        $ zypper install orthos2

2. Enter the correct server name to the nginx server conf:
    In ``/etc/nginx/conf.d/orthos2_nginx.conf`` replace ``127.0.0.1`` in the ``server_name`` directive with the fqdn of
    the orthos2 server

3. Deploy code to database

  .. code-block::

    orthos-admin migrate

4. Install fixtures (push data to database; optional):

   In case you want to load data from another orthos instance where you
   previously dumped data tables:

   .. code-block::

       orthos-admin loaddata "dump.json"


5. Create a superuser
    .. code-block::

        orthos-admin createsuperuser

6. Create html files from templates
    .. code-block::

        orthos-admin collectstatic

7. start all services
    .. code-block::

        systemctl enable --now nginx
        systemctl enable --now orthos2.service
        systemctl enable --now orthos2_taskmanager


Setup a Cobbler Server
######################

Setting up a Cobbler server is important to be able to manage the DHCP and DNS of a network. Power operations of systems
are managed through Cobbler as well.

1. Install Cobbler: ``zypper in cobbler``

2. Modify the following settings and adjust them to your network:

    * ``bind_master``
    * ``manage_dhcp``
    * ``manage_dhcp_v4``
    * ``manage_dhcp_v6``
    * ``manage_dns``
    * ``manage_forward_zones``
    * ``manage_reverse_zones``
    * ``manage_tftpd``
    * ``next_server_v4``
    * ``next_server_v6``
    * ``scm_track_*``
    * ``server``

3. Start the Cobbler server: ``systemctl enable --now cobblerd``

4. Generate the networked bootloaders: ``cobbler mkloaders``

5. Run an initial synchronization: ``cobbler sync``

.. note:: How you manage the Cobbler Distros and Profiles to make them available is specifc to your Orthos 2
          instance. SUSE is using the Cobbler Terraform Provider along with an internal GitLab CI pipeline to provision
          Cobbler Distros and Profiles.

Optional: Setup cscreen server
##############################

The Domain feature of "cscreen" server (`github.com/openSUSE/cscreen <https://github.com/openSUSE/cscreen>`_) requires
the manual setup of a cscreen server. Follow these steps to ensure that Orthos can regenerate the configuration:

1. Install cscreen (openSUSE ``zypper in cscreen``)

2. Install the cscreen sudoers configuration
   .. code-block::

       %_cscreen ALL= NOPASSWD: /usr/bin/systemctl restart cscreend.service

3. Setup passwordless SSH keys between the ``orthos`` (Orthos server) to the ``_cscreen`` user (console server).

4. Enable and start the systemd service for cscreen ``systemctl enable --now cscreend.service``
