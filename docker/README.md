# Development Container

The workflow is as follows (from the project root folder):

```shell
podman build -f docker/develop.dockerfile -t orthos2-dev:latest .
podman run -it --entrypoint="/bin/bash" -v $PWD:/code --rm -p 8000:8000 localhost/orthos2-dev:latest
```

If you are inside the container the usage is as follows:

```shell
python3 manage.py test
```

Now if you want to serve the webinterface you need to do something a little weird:

```shell
/code/docker/devel-server.sh
```

If you messed something up just hit "Ctrl + C" and "Ctrl + D" and use the `podman run ...` command to spawn a new
container.

What might be useful is if you load some default fixtures for testing:

```shell
python3 manage.py loaddata orthos2/data/fixtures/architectures.json
python3 manage.py loaddata orthos2/data/fixtures/platforms.json
python3 manage.py loaddata orthos2/data/fixtures/serialconsoletypes.json
python3 manage.py loaddata orthos2/data/fixtures/systems.json
```
