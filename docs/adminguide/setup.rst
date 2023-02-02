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

        orthos-admin makemigrations data frontend taskmanager api
    
5. Deploy code to database
   
   a. In case of a fresh install - Create the database:
      .. code-block::

        orthos-admin migrate

   b. In case of an Update (and makemigrations above produced database difference
      dumps) - Apply/deploy detected database changes
      In case of changes detected in the data app, do:
      .. code-block::
	 
       orthos-admin migrate data

6. Install fixtures (push data to database):

   a. In case of a fresh install - Load data from package data:

    .. code-block::

        orthos-admin loaddata /usr/share/orthos2/fixtures/data/*.json /usr/share/orthos2/fixtures/taskmanager/*.json


   b. In case you want to load data from another orthos instance where you
      previously dumped data tables:

    .. code-block::

        orthos-admin loaddata "dumped_table.json"


7. Create a superuser
    .. code-block::

        orthos-admin createsuperuser

8. Create html files from templates
    .. code-block::

        orthos-admin collectstatic

9. start all services
    .. code-block::

        systemctl enable nginx
        systemctl enable orthos2.socket
        systemctl enable orthos2.service
        systemctl enable orthos2_taskmanager

        systemctl start nginx
        systemctl start orthos2.socket
        systemctl start orthos2.service
        systemctl start orthos2_taskmanager
