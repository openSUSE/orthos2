**************************************
Installation/Setup (Production system)
**************************************

1. Install the orthos2 package:
    .. code-block::

        $ zypper install orthos2

2. Change nginx user to orthos:
    In ``/etc/nginx/nginx.conf`` add ``user  orthos orthos;`` to the beginning of the file

3. Enter the correct server name to the nginx server conf:
    In ``/etc/nginx/conf.d/orthos2_nginx.conf`` replace ``127.0.0.1`` in the ``server_name`` directive with the fqdn of
    the orthos2 server

4. Deploy code to database

  .. code-block::

    orthos-admin migrate

5. Install fixtures (push data to database; optional):

   In case you want to load data from another orthos instance where you
   previously dumped data tables:

   .. code-block::

       orthos-admin loaddata "dump.json"


6. Create a superuser
    .. code-block::

        orthos-admin createsuperuser

7. Create html files from templates
    .. code-block::

        orthos-admin collectstatic

8. start all services
    .. code-block::

        systemctl enable nginx
        systemctl enable orthos2.service
        systemctl enable orthos2_taskmanager

        systemctl start nginx
        systemctl start orthos2.service
        systemctl start orthos2_taskmanager

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
