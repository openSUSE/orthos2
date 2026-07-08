*********************************
Installation/Setup (Docker)
*********************************


1. Set up external dependencies
    Orthos2 requires a Netbox instance, an Authentication provider (like Authentik), a DB (like Postgres), and Cobbler, which need to be set up

2. Create the secrets `NetboxToken`, `OIDCsecret`, `OrthosKey`, and `SCCcredentials` in `docker/secrets/`
    Instructions for creating `SCCcredentials` can be found `here <https://opensource.suse.com/bci-docs/guides/container-suseconnect/>`, the rest you will need to supply yourself.
    Create the secrets like this:
    .. code-block::
        
        echo "[Token]" > docker/secrets/NetboxToken
        echo "[OIDC key]" > docker/secrets/OIDCsecret
        echo "[Orthos key]" > docker/secrets/OrthosKey

3. Fill out .env files
    The .env at the root of the project needs to be filled out.

4. Start the containers 
    .. code-block::

        docker compose up -d

    After the containers have started, you can view their logs and make sure they're running correctly using
    .. code-block::

        docker compose logs -f

5. Updating the containers
    If you need to update the containers in future, simply stop the containers, update them, and start them again
    .. code-block::

        docker compose down
        docker compose pull
        docker compose up -d