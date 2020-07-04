# Installation/Setup

## Initial setup (development)

1. Prepare your local system:
    ```sh
    $ sudo zypper in python3-pip python3-virtualenv python3-devel libopenssl-devel
    ```

2. Check out the sources:
    ```sh
    $ git clone git@github.com:openSUSE/orthos2.git
    $ cd orthos2/
    ```

3. Create the virtual Python environment ([virtualenv](https://virtualenv.pypa.io/en/stable/)), activate it and update [pip](https://en.wikipedia.org/wiki/Pip_(package_manager)):
    ```sh
    $ virtualenv .env
    Using base prefix '/usr'
    New python executable in .env/bin/python3
    Also creating executable in .env/bin/python
    Installing setuptools, pip, wheel...done.
    $ . .env/bin/activate
    $ pip install --upgrade pip
    Collecting pip
    ...
    ```

4. Install the required Python modules for development:
    ```sh
    $ pip install -r requirements-devel.txt
    Collecting django
    ...
    $ cd orthos2/
    ```

5. Migrate (create) the database:
    ```sh
    $ python manage.py migrate
    Operations to perform:
            Apply all migrations: admin, auth, authtoken, contenttypes, data, sessions, taskmanager
    Running migrations:
            Applying ...
    ```

6. Load initial data:
    ```sh
    $ python manage.py loaddata data/fixtures/*.json
    Installed 94 object(s) from 7 fixture(s)
    $ python manage.py loaddata taskmanager/fixtures/*.json
    Installed 2 object(s) from 1 fixture(s)
    ```

7. Create a superuser (administrator) account:
    ```sh
    $ python manage.py createsuperuser
    Username (leave blank to use '<your_login>'): admin
    Email address: <your_login>@domain.de
    Password: ********
    Password (again): ********
    Superuser created successfully.
    ```

8. Run the test server:
    ```sh
    $ python manage.py runserver localhost:8000
    Performing system checks...
    System check identified no issues (0 silenced).
    November 23, 2017 - 16:25:35
    Django version 1.11.7, using settings 'orthos2.settings'
    Starting development server at http://localhost:8000/
    Quit the server with CONTROL-C.
    ```

9. Open your browser and go to [http://localhost:8000](http://localhost:8000) or [http://localhost:8000/admin](http://localhost:8000/admin) (use the superuser login here)

## Initial setup (production)
