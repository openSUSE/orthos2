"""
Registers the orthos2 dev stack's custom DHCPv4/v6 templates (docker/orthos/cobbler-templates/)
as active Cobbler Template items, so `cobbler sync` renders subnets for "192.0.2.0/24" (IPv4) and
"2001:db8::/64" (IPv6) instead of the built-in example templates. Run inside the "orthos2"
container via:

    python3.11 manage.py shell </code/docker/orthos/setup_cobbler_dhcp_templates.py

Idempotent - safe to re-run; existing items are left as-is.

Cobbler >=4.0.0 no longer reads a fixed filesystem path like /etc/cobbler/dhcp.template at
render time (see docs/user-guide/templating.rst) - modules.managers.isc looks up a Template item
by tag instead (api.find_template(tags=<"dhcpv4"|"dhcpv6">), preferring one tagged "active" over
one tagged "default"). Registering one is therefore a two-step process: the actual template file
has to already exist under settings.autoinstall_templates_dir (done here by compose.common.yaml's
"cobblerd" service mounting the "cobbler-dhcp-template"/"cobbler-dhcpv6-template" configs into
/var/lib/cobbler/templates/), then a Template item is created pointing at it by relative path.
"""

import xmlrpc.client  # nosec: B411

from orthos2.data.models import Domain

DOMAIN_NAME = "orthos2.test"

# (template name, relative path under /var/lib/cobbler/templates, tag)
TEMPLATES = [
    ("orthos2-dhcpv4", "orthos2-dhcp.template", "dhcpv4"),
    ("orthos2-dhcpv6", "orthos2-dhcp6.template", "dhcpv6"),
]


def register_template(
    server: xmlrpc.client.Server, token: str, name: str, path: str, tag: str
) -> None:
    if server.has_item("template", name, token):
        print(f'Template "{name}" already exists, skipping.')
        return

    template_id = server.new_template(token)
    server.modify_template(template_id, ["name"], name, token)
    server.modify_template(template_id, ["template_type"], "cheetah", token)
    server.modify_template(template_id, ["uri", "schema"], "file", token)
    server.modify_template(template_id, ["uri", "path"], path, token)
    # "active" beats a "default"-tagged template (the built-in one) for the same tag - see
    # cobbler/modules/managers/isc.py's _write_config().
    server.modify_template(template_id, ["tags"], [tag, "active"], token)
    server.save_template(template_id, True, True, "new", token)
    print(f'Created template "{name}" (tags: {tag}, active).')


def main() -> None:
    domain = Domain.objects.get(name=DOMAIN_NAME)
    if not domain.cobbler_server:
        raise RuntimeError(f'Domain "{DOMAIN_NAME}" has no Cobbler server configured!')

    server = xmlrpc.client.Server(  # nosec: B411
        f"http://{domain.cobbler_server.fqdn}/cobbler_api"
    )
    token = server.login(domain.cobbler_server_username, domain.cobbler_server_password)

    for name, path, tag in TEMPLATES:
        register_template(server, token, name, path, tag)


main()
