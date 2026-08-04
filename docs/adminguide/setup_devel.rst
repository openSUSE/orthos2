*********************************
Installation/Setup (Devel system)
*********************************

1. Prepare your local system:

   .. code-block::

       $ sudo zypper in docker docker-compose gcc python3-devel jq make


2. Check out the sources:

   .. code-block::

       $ git clone git@github.com:openSUSE/orthos2.git
       $ cd orthos2/

.. If we do a linebreak in the following line the formatting is messed up. Let it be!

3. Create the `virtual Python environment <https://docs.python.org/3/library/venv.html>`_, activate it and update `pip <https://en.wikipedia.org/wiki/Pip_(package_manager)>`_

   .. code-block::

       $ python3 -m venv .venv
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

      $ python3 docker/manage-secrets.py

6. Setting up the SSC credentials for docker:

   .. code-block::
        get a registration code from SUSE Customer Center
       $ docker run --rm registry.suse.com/suse/sle15:latest bash -c \
            "zypper -n in SUSEConnect; SUSEConnect --regcode YOUR_REGISTRATION_CODE; \
            cat /etc/zypp/credentials.d/SCCcredentials"

   (if you don't use Docker `click here for more information <https://opensource.suse.com/bci-docs/guides/container-suseconnect>`__)

7. Create a file for credentials (line for line):

   .. code-block::

      $ cat <<EOF > ./docker/secrets/SCCcredentials
       username=SCC_xxx
       password=xxx
       system_token=xxx
       EOF

8. Run the test server:

   .. code-block::

      $ make up-dev

   If you wish to test for the production environment instead, use the ``Makefile`` target below.
   It automatically provisions a NetBox API token as the ``docker/secrets/NetboxToken`` Docker
   secret before starting the stack, so no manual steps are needed:

   .. code-block::

       $ make up-testing

9. Edit your ``/etc/hosts`` file and include the following line:

   .. code-block::

      127.0.0.1 authentik.orthos2.test orthos2.orthos2.test cobbler.orthos2.test netbox.orthos2.test testmachine.orthos2.test

10. Open your browser and go to `http://orthos2.orthos2.test <http://orthos2.orthos2.test>`_.
     Now you have to change the URL from:
        "https://orthos2.orthos2.test/login/?next=/machines/free"
     to:
        "https://orthos2.orthos2.test/login/?builtin=true"

11. LogIn:
    you can find the login password for the admin user in ``./docker/orthos/orthos2dev.env``
    Enjoy.
