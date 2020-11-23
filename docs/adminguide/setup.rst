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

4. Dump Database Model:
    .. code-block::

        cd /usr/lib/orthos2
        sudo -u orthos ./manage.py makemigrations data frontend taskmanager api
    
5. Deploy code to database
   
   a. In case of a fresh install - Create the database:
      .. code-block::

        cd /usr/lib/orthos2
        sudo -u orthos ./manage.py migrate

   b. In case of an Update (and makemigrations above produced database difference
      dumps) - Apply/deploy detected database changes
      In case of changes detected in the data app, do:
      .. code-block::
	 
       cd /usr/lib/orthos2
       sudo -u orthos ./manage.py migrate data

6. Install fixtures:
    .. code-block::

        sudo -u orthos ./install_all_fixtures.sh

7. Create a superuser
    .. code-block::

        sudo -u orthos ./manage.py createsuperuser

8. start all services
    .. code-block::

        systemctl enable nginx
        systemctl enable orthos2.socket
        systemctl enable orthos2.service
        systemctl enable orthos2_taskmanager

        systemctl start nginx
        systemctl start orthos2.socket
        systemctl start orthos2.service
        systemctl start orthos2_taskmanager
