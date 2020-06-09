# Administrator`s Guide

Overview:

* [Machines](./adminguide/machine.md)
* [Server Configuration](#server-configuration)
* [WebSockets](./adminguide/websocket.md)

---

## Server Configuration

### `ssh.keys.paths`

File path(s) to private SSH keys. Multiple paths can be separated by a comma.
In production mode (running e.g on Apache webserver), absolute paths should be used.
Each SSH connection tries all keys until one of them matches.

Default: `./keys/orthos2-master-test`

Example: `/root/.ssh/id_rsa_cobbler_server, /root/.ssh/id_rsa_sconsole`

---

### `ssh.timeout.seconds`

Set the SSH connecting timeout (in seconds).

Default: `10`

---

### `ssh.scripts.remote.directory`

Remote directory where scripts get copied before they get run on the remote system.

Default: `/tmp/orthos-scripts`

---

### `ssh.scripts.local.directory`

Local directory holding scripts determined for remote execution (e.g. for machine checks).

Default: `./scripts`

---

### `domain.validendings`

List of valid network domain endings. All FQDN's must match at least one of these.
Multiple endings can be separated by a comma.

Default: `example.de, example.com`

Example: `example.de, example.com, example.bayern`

---

### `tasks.daily.executiontime`

Time at which the daily tasks are started. Must be in 24h format.

Default: `00:00`

---

### `mail.smtprelay.fqdn`

The SMTP server that is used to send mails. That should be a company-internal server.

Default: `relay.mail-server.de`

---

### `mail.subject.prefix`

Subject prefix of the emails sent by Orthos. Each mail gets the prefix before the subject itself (e.g.: `[ORTHOS] Orthos password restored`).
A whitespace after the prefix is recommended.

Default: `[ORTHOS]<whitespace>`

---

### `mail.from.address`

Sender field of the emails sent by Orthos.

Default: `orthos-noreply@domain.de`

---

### `serialization.output.directory`

Local directory where the machine object copies are stored after deleting a machine
(see [Machines](./adminguide/machine.md) for more information).

Default: `/tmp`

Example: `/usr/share/grave`

---

### `serialization.output.format`

Data format for the machine object copies after deleting a machine. Valid formats
are `json` and `yaml` (see [Machines](./adminguide/machine.md) for more information).

Default: `json`

Example: `yaml`

---

### `websocket.cscreen.command`

Local command which gets executed when a serial console gets requested. The
service appends the hostname to the command (e.g. `/usr/bin/screen host`).
The command can be anything returning a terminal
(see [WebSockets](./adminguide/websocket.md) for more information).


Default: `/usr/bin/screen`

---

### `websocket.port`

The port on which the WebSocket service is listening
(see [WebSockets](./adminguide/websocket.md) for more information).

Default: `8010`