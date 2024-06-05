"""""""""""""
Orthos Client
"""""""""""""

Command Line Interface (CLI)
############################

Basics
======

The Orthos CLI is a simple interactive shell. You can perform following tasks with the Orthos CLI:

- execute complex queries such as “which machines have more than 4 CPUs” and are reserved by Manfred
- reserve or release a machine
- trigger installation of a machine
- view detailed machine information (such as dmidecode, lspci, lsmod or hwinfo)
- turn power on/off or just reboot a machine
- edit machine data
- Sync machines with a cobbler server
- Trigger machine data scans
- ...

Install the CLI
===============

Python 3 is recommended.

.. code-block::

    zypper in orthos-client

In the Orthos Web Client you will find also the download link ``Download CLI`` to the CLI, here you have the possibility
to download the suitable client for your distribution(.rpm). The button is in the top right corner.

Connecting the CLI to the Orthos Server
=======================================

The CLI has several options how you can set up the connection to the Orthos server and adapt it to your needs.

.. code-block::

    you_machine:~ # orthos --help
    usage: orthos [-h] [-H HOST] [-P PORT] [-U USER] [--password PASSWORD]
                  [--token TOKEN] [-D] [-L FILE] [--no-pager] [-p] [-F IFS]
                  [-q] [-v] [--timezone TZ]

    Orthos command line interface.

    optional arguments:
      -h, --help            show this help message and exit
      -H HOST, --host HOST  use the hostname specified on the command line instead
                            of the one in the config file
      -P PORT, --port PORT  use the port specified on the command line instead of
                            the one in the config file
      -U USER, --user USER  use the username specified
      --password PASSWORD   Better use --token instead (Create a token in the
                            preferences section of the user on the web
			    interface of the server)
      --token TOKEN         use this token for automatic authentication (e.g. for
                            scripting); -U/--password options will be ignored
      -D, --debug           write debugging output
      -L FILE, --logfile FILE
                            use that together with -D to log the debug output in a
                            file rather than the console
      --no-pager            do not use pager when showing results
      -p, --plain-output    print plain output (e.g. for scripting)
      -F IFS, --ifs IFS     set internal field separator (only useful in
                            combination with -p; default is $OIFS)
      -q, --quiet           makes command line client quiet
      -v, --version         print version output
      --timezone TZ         set the local time zone (default is "Europe/Berlin")

Example for the connection to the Orthos Server:

.. code-block::

    your_machine:~ # orthos -H https://orthos-next.arch.suse.de
    (orthos 2.0.0)

Orthosrc configuration file
===========================

The orthos package installs an empty configuration file in |orthosrc_loc|. Once you connected to the orthos server, it
is recommended to copy this file to your local config directory: ``~/.config/orthosrc`` and adapt the file to your
needs.

The file follows the following format: `Python 3 Docs - Supported INI file structure <https://docs.python.org/3/library/configparser.html#supported-ini-file-structure>`_

The CLI will read the global configuration file found at ``/etc/orthosrc`` and after that load the user config file.
There are two sections:

* ``global``: Keys for username, server, port, protocol and the token.
* ``alias``: Keys are the name of the alias whereas the value is the query that is being sent.

For authentication it is required to obtain a token from the WebUI under "Preferences".

Orthos Command Examples
=======================

HELP

Provides help and shows you an overview of the available Orthos CLI commands.

.. code-block::

    (orthos 2.0.0) help

    Commands are:

    INFO                 Retrieve information about a machine.
    POWER                Power cycles a machine.
    REGENERATE           Regenerate machine-related or service files.
    RESCAN               Rescan a machine.
    SERVERCONFIG         Show server configuration.
    RESERVATIONHISTORY   Show reservation history of a machine.
    ADD                  Adds information to the database.
    RELEASE              Release machines.
    QUERY                Retrieve information about a machine.
    RESERVE              Reserve machines.
    SETUP                Automatic machine setup.
    DELETE               Removes information from the database.
    ALIAS                Define own aliases.
    AUTH                 Request authorisation manually.
    EXIT                 Exit program.
    HELP                 Provides help.


.. code-block::

    (orthos 2.0.0) help info
    Command to get information about a machine.

    Usage:
        INFO <fqdn>

    Arguments:
        fqdn - FQDN or hostname of the machine.

    Example:
        INFO foo.suse.de


.. code-block::

    (orthos 2.0.0) help power
    Command to power cycle machines or the get the current status.

    Usage:
        POWER <fqdn> <action>

    Arguments:
        fqdn   - FQDN or hostname of the machine.
        action - Specify new power state. Actions are:

    on                 : Power on.
    off                : Power off via SSH. If didn't succeed, use remote power.
    off-ssh            : Power off via SSH only.
    off-remotepower    : Power off via remote power only.
    reboot             : Reboot via SSH. If didn't succeed, use remote power.
    reboot-ssh         : Reboot via SSH only.
    reboot-remotepower : Reboot via remote power only.
    status             : Get power status.

    Example:
        POWER foo.suse.de reboot


.. code-block::

    (orthos 2.0.0) help reserve
    Reserves a machine.

    Usage:
        RESERVE <fqdn>

    Arguments:
        fqdn - FQDN or hostname of the machine.

    Example:
        RESERVE foo.suse.de



.. code-block::

    (orthos 2.0.0) help alias
    Define or display aliases. The command can be called without any arguments, then it displays all available aliases. If it's called with one argument, then it displays the definition of a specific alias. If it is called with more than two arguments, then you can define new aliases.

    To execute an alias, type the alias name with a leading '@'.

    Usage:
        ALIAS [alias] [*args]

    Arguments:
        alias - Alias name.
        *args - Valid command string.

    Example:
        ALIAS
        ALIAS allmachines query name, ipv4 where name =~ foobar
        ALIAS allmachines

    @allmachines


QUERY

Retrieve all kind of information about a machine or general orthos data.
This is a very powerful command. It is built up similar to a SELECT SQL
database statement. In fact it ends up in querying the underlying orthos
server database:

query foo, bar where binary_attribute and int_attribute > XY and char_attribute
=~ "STRING"

-> This will search for and show the results (also attributes): foo and bar
where the condition after where matches.

Examples:

.. code-block::

    query fqdn, cpu_physical
    query fqdn where cpu_model =~ Intel
    query fqdn where cpu_model =~ Intel OR !efi


More complex queries:

.. code-block::

    # Show full names and installed distributions of all machines which
    # are not reserved (!res_by), which do run and have an orthos ssh key
    # installed and therefore could be nightly scanned (status_login)
    # which are not administrative, x86_64 machines and do have more than 7
    # CPU cores:
    query fqdn, inst_dist where !res_by and status_login and !administrative and architecture = x86_64 and cpu_cores > 7


Use alias(es) for more complex queries:
To permanently define and use above command as an alias (auto-stored in
~/.config/orthosrc), make sure to not use any quoting, just do:

.. code-block::

   alias x86_free_running query fqdn, inst_dist where !res_by and status_login and !administrative and architecture = x86_64 and cpu_cores > 7



To use above defined alias (tab completion working...):

.. code-block::

   @x86_free_running


Valid operators are:

.. code-block::

    !<field>            not (binary fields only)
    == =                exactly equal
    =~                  contains
    =*                  startswith
    !=                  unequal
    >  <                greater or less than (number fields only)
    >= <=               greater equals or less equals (number fields only)
    AND                 logical conjunction
    OR                  logical disjunction


Orthos Variables and Objects
============================

The Orthos Client has many objects that you can query from the machine objects
in Orthos. The names are self-explanatory and can be used for queries
as described under the `query` command above or you use the TAB completion
feature to see available `query` attributes.
