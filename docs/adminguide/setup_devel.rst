*********************************
Installation/Setup (Devel system)
*********************************

1. Prepare your local system:
    .. code-block::

        $ sudo zypper in docker docker-compose openldap2-devel cyrus-sasl-devel


2. Check out the sources:
    .. code-block::

        $ git clone git@github.com:openSUSE/orthos2.git
        $ cd orthos2/

.. If we do a linebreak in the following line the formatting is messed up. Let it be!

3. Create the `virtual Python environment <https://docs.python.org/3/library/venv.html>`_, activate it and update `pip <https://en.wikipedia.org/wiki/Pip_(package_manager)>`_
    .. code-block::

        $ python -m venv .venv
        $ . .venv/bin/activate
        $ pip install --upgrade pip
        Collecting pip
        ...

4. Install the required Python modules for development:
    .. code-block::

        $ pip install -r requirements-devel.txt -r docs/requirements.docs.txt
        Collecting django
        ...

5. Generate the required secrets to bring up the Docker Compose Stack:
    .. code-block::

        python3 docker/manage-secrets.py

6. Run the test server:
    .. code-block::

        docker compose up -d

7. Edit your ``/etc/hosts`` file and include the following line:
    .. code-block::

        127.0.0.1 orthos2.orthos2.test cobbler.orthos2.test netbox.orthos2.test

8.  Open your browser and go to `http://orthos2.orthos2.test <http://orthos2.orthos2.test>`_ (use the superuser login 
    here). The login password for the admin user you can find in ``docker/orthos/orthos2.env``.
