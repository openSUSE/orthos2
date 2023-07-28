# Development Container

The workflow is as follows (from the project root folder):

```shell
podman build -f docker/develop.dockerfile -t orthos2-dev:latest .
podman run -it -v $PWD:/code --rm -p 8000:8000 localhost/orthos2-dev:latest
```

If you are inside the container the usage is as follows:

```shell
pip install -r requirements-devel.txt
sudo -u orthos bash
python3 manage.py test
```

Now if you want to serve the webinterface you need to do something a little weird:

```shell
# Start as root
sudo -u orthos bash
python3 manage.py migrate
DJANGO_SUPERUSER_PASSWORD="admin" python3 manage.py createsuperuser --noinput --username admin --email admin@example.com
python3 manage.py runserver 0.0.0.0:8000
```

If you messed something up just hit "Ctrl + D" two times and use the `podman run ...` command to spawn a new container.
