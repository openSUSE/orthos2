# Development Container

The workflow is as follows (from the project root folder):

```shell
podman build -f docker/develop.dockerfile -t orthos2-dev:latest .
podman run -it -v $PWD:/code --rm -p 8000:8000 localhost/orthos2-dev:latest
```

If you are inside the container the usage is as follows:

```shell
pip install -r requirements-devel.txt
su - orthos
python3 manage.py test
```

If you messed something up just hit "Ctrl + D" two times and use the `podman run ...` command to spawn a new container.
