********
Machines
********

Delete a machine
################

To delete a machine, choose from the machine list and press 'Delete' at the bottom of the machine view. All related
information that is also deleted together with the machine object is displayed. Press ``Yes`` to confirm. For
administrative reasons, a copy of each deleted machine object is stored in the form of a file. The format (JSON, Yaml)
as well as the target directory can be set via the server configuration.

Further configuraton information can be found in the :ref:`admin-guide` (``serialization.*``).

.. note::

    When running in production mode, make sure the target directory (``serialization.output.directory``) can be written
    by the webserver user - this also affects the default ``/tmp`` directory
    (`more information <http://blog.oddbit.com/2012/11/05/fedora-private-tmp/>`_).
