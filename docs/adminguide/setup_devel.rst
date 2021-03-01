*********************************
Installation/Setup (Devel system)
*********************************

1. Prepare your local system:
    .. code-block::

        $ sudo zypper in python3-pip python3-virtualenv python3-devel libopenssl-devel openldap2-devel


2. Check out the sources:
    .. code-block::

        $ git clone git@github.com:openSUSE/orthos2.git
        $ cd orthos2/

.. If we do a linebreak in the following line the formatting is messed up. Let it be!

3. Create the virtual Python environment (`virtualenv <https://virtualenv.pypa.io/en/stable/>`_), activate it and update `pip <https://en.wikipedia.org/wiki/Pip_(package_manager)>`_
    .. code-block::

        $ virtualenv .env
        Using base prefix '/usr'
        New python executable in .env/bin/python3
        Also creating executable in .env/bin/python
        Installing setuptools, pip, wheel...done.
        $ . .env/bin/activate
        $ pip install --upgrade pip
        Collecting pip
        ...

4. Install the required Python modules for development:
    .. code-block::

        $ pip install -r requirements-devel.txt
        Collecting django
        ...
        $ cd orthos2/

   Set environment variables for development:
    .. code-block::

        $ export PYTHONPATH=$(git rev-parse --show-toplevel)
        $ export ORTHOS_DEV=1

5. Dump Database Model:
    .. code-block::

        $ cd bin/
        $ python manage.py makemigrations data frontend taskmanager api

6. Migrate (create) the database:
    .. code-block::

         $ python manage.py migrate
         Operations to perform:
                 Apply all migrations: admin, auth, authtoken, contenttypes, data, sessions, taskmanager
         Running migrations:
                 Applying ...

7. Load initial data:
    .. code-block::

        $ python manage.py loaddata ../data/fixtures/*.json
        Installed 94 object(s) from 7 fixture(s)
        $ python manage.py loaddata ../taskmanager/fixtures/*.json
        Installed 2 object(s) from 1 fixture(s)

8. Create a superuser (administrator) account:
    .. code-block::

        $ python manage.py createsuperuser
        Username (leave blank to use '<your_login>'): admin
        Email address: <your_login>@domain.de
        Password: ********
        Password (again): ********
        Superuser created successfully.

9. Run the test server:
    .. code-block::

        $ python manage.py runserver localhost:8000
        Performing system checks...
        System check identified no issues (0 silenced).
        November 23, 2017 - 16:25:35
        Django version 1.11.7, using settings 'orthos2.settings'
        Starting development server at http://localhost:8000/
        Quit the server with CONTROL-C.

10. Open your browser and go to `http://localhost:8000 <http://localhost:8000>`_ or
   `http://localhost:8000/admin <http://localhost:8000/admin>`_ (use the superuser login here).
