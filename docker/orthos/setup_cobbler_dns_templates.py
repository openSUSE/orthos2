"""
Registers the orthos2 dev stack's fixed "named_primary" template (docker/orthos/cobbler-templates/
named.template) as the active Cobbler Template item, so the "cobbler-dns" sidecar actually starts.
Run inside the "orthos2" container via:

    python3.11 manage.py shell </code/docker/orthos/setup_cobbler_dns_templates.py

Idempotent - safe to re-run; an existing item is left as-is.

The built-in "named_primary" template's "logging" block writes to a relative path ("data/named.run")
whose parent directory nothing ever creates, so named fails validating its own config at startup
("checking logging configuration failed: file not found") before it gets anywhere near loading
zones. See docker/orthos/cobbler-templates/named.template's own comment for the fix. Same
file-must-already-exist-on-the-server mechanism as docker/orthos/setup_cobbler_dhcp_templates.py -
compose.common.yaml's "cobblerd" service mounts the "cobbler-named-template" config into
/var/lib/cobbler/templates/ for this to point at.
"""

import xmlrpc.client  # nosec: B411

from orthos2.data.models import Domain

DOMAIN_NAME = "orthos2.test"

TEMPLATE_NAME = "orthos2-named-primary"
TEMPLATE_PATH = "orthos2-named.template"
TEMPLATE_TAG = "named_primary"


def main() -> None:
    domain = Domain.objects.get(name=DOMAIN_NAME)
    if not domain.cobbler_server:
        raise RuntimeError(f'Domain "{DOMAIN_NAME}" has no Cobbler server configured!')

    server = xmlrpc.client.Server(  # nosec: B411
        f"http://{domain.cobbler_server.fqdn}/cobbler_api"
    )
    token = server.login(domain.cobbler_server_username, domain.cobbler_server_password)

    if server.has_item("template", TEMPLATE_NAME, token):
        print(f'Template "{TEMPLATE_NAME}" already exists, skipping.')
        return

    template_id = server.new_template(token)
    server.modify_template(template_id, ["name"], TEMPLATE_NAME, token)
    server.modify_template(template_id, ["template_type"], "cheetah", token)
    server.modify_template(template_id, ["uri", "schema"], "file", token)
    server.modify_template(template_id, ["uri", "path"], TEMPLATE_PATH, token)
    # "active" beats a "default"-tagged template (the built-in one) for the same tag - see
    # cobbler/modules/managers/bind.py's __write_named_conf().
    server.modify_template(template_id, ["tags"], [TEMPLATE_TAG, "active"], token)
    server.save_template(template_id, True, True, "new", token)
    print(f'Created template "{TEMPLATE_NAME}" (tags: {TEMPLATE_TAG}, active).')


main()
