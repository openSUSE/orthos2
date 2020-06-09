# WebSockets

## Serial console in the web browser

Orthos provides the ability to use an interactive serial console in the web browser for each machine
that has an entry for a serial console. The WebSocket communication protocol is used for this.
To start the WebSocket service, the following command line must be executed (no HTTPS/TLS):

```sh
$ python manage.py serialconsole-ws --start
Start websocket daemon on port 8010...
```

With HTTPS/TLS:

```sh
$ python manage.py serialconsole-ws --start --wss\
    --crt <certificate>\
    --key <key>
Start websocket daemon on port 8010...
```

Example:

```sh
$ python manage.py serialconsole-ws --start --wss\
    --crt /etc/apache2/ssl.crt/orthos.network.tld.crt\
    --key /etc/apache2/ssl.key/orthos.network.tld.pem
Start websocket daemon on port 8010...
```

Further configuraton information can be found in the [Administrator`s Guide](../adminguide.md)
(`websocket.*`).

When the service establishes a SSH connection to invoke a command on a remote
server, a SSH key without password is recommendend. The key path just needs to
be added to the SSH command (`-i <identity_file>`).

The output is available in the machine view under the tab 'Serial Console'.

This feature was tested with Chromium Version 62.0.3202.89 (64-bit) and
Firefox 52.5.0 (64-bit).
