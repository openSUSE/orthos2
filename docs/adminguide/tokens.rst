******
Tokens
******

Usually no administration is required for tokens. When users use the command line client for the first time, they must
authenticate themselves with the user / password, after which a token is written for the user. After the process, it is
no longer necessary to log on via CLI, since this is then done via the token.

.. code-block::

    -----------------
    |      CLI      |         -----------------
    | User/Password |---->----|               |
    -----------------         | Orthos Server |
    -----------------         | User -> Token |
    |      CLI      |----<----|               |
    | User / Token  |         -----------------
    -----------------