"""
Creates a fake Cobbler Distro+Profile pair for local dev-stack experimentation, so a Machine can be
set up in Orthos 2 without a real distro tree. Run inside the "orthos2" container via:

    python3.11 manage.py shell </code/docker/orthos/setup_fake_cobbler_distro.py

Idempotent - safe to re-run; existing items are left as-is.

Cobbler profile names are not validated by Orthos 2, but two call sites impose a de-facto schema
(see orthos2/utils/cobbler.py's CobblerServer.get_profiles()/setup(), and
orthos2/data/models/domain.py's Domain.get_setup_records*()):

  * get_profiles() lists profiles via a Cobbler wildcard search on "<architecture>*", so the
    profile name must start with the architecture name.
  * setup() reconstructs the profile name as f"{machine.architecture}:{choice}", where "choice" is
    whatever get_setup_records*() returned - which strips a leading "<arch>:" segment when the raw
    Cobbler name has two colons. For that round-trip to land back on the real profile, the name must
    be the 3-segment form: "<architecture>:<distro-name>:<install-choice>".
"""

import os
import xmlrpc.client  # nosec: B411

from orthos2.data.models import Architecture, Domain

DOMAIN_NAME = "orthos2.test"
ARCHITECTURE_NAME = "x86_64"
DISTRO_LABEL = "FAKE-1.0"
INSTALL_CHOICE = "install"

DISTRO_NAME = f"{ARCHITECTURE_NAME}:{DISTRO_LABEL}"
PROFILE_NAME = f"{ARCHITECTURE_NAME}:{DISTRO_LABEL}:{INSTALL_CHOICE}"

# Bind-mounted read-only into cobblerd/http-api at this same path (see compose.common.yaml's
# "cobblerd"/"http-api" services) from "./distro-sources" at the repository root - which is also
# where this container sees it, at "/code/distro-sources", since the whole repo is bind-mounted at
# "/code". Cobbler's own kernel-filename check requires the basename "vmlinuz" (or a handful of other
# recognized kernel names); the initrd name is unconstrained.
DISTRO_SOURCE_DIR_IN_ORTHOS2 = f"/code/distro-sources/{DISTRO_LABEL}"
DISTRO_SOURCE_DIR_IN_COBBLERD = f"/srv/distro-sources/{DISTRO_LABEL}"


def create_fake_kernel_and_initrd() -> None:
    os.makedirs(DISTRO_SOURCE_DIR_IN_ORTHOS2, exist_ok=True)
    kernel_path = os.path.join(DISTRO_SOURCE_DIR_IN_ORTHOS2, "vmlinuz")
    initrd_path = os.path.join(DISTRO_SOURCE_DIR_IN_ORTHOS2, "initrd.img")
    if not os.path.exists(kernel_path):
        with open(kernel_path, "w", encoding="utf-8") as kernel_file:
            kernel_file.write("FAKE-KERNEL-FOR-ORTHOS2-TESTING\n")
    if not os.path.exists(initrd_path):
        with open(initrd_path, "w", encoding="utf-8") as initrd_file:
            initrd_file.write("FAKE-INITRD-FOR-ORTHOS2-TESTING\n")


def main() -> None:
    create_fake_kernel_and_initrd()

    domain = Domain.objects.get(name=DOMAIN_NAME)
    if not domain.cobbler_server:
        raise RuntimeError(f'Domain "{DOMAIN_NAME}" has no Cobbler server configured!')

    server = xmlrpc.client.Server(  # nosec: B411
        f"http://{domain.cobbler_server.fqdn}/cobbler_api"
    )
    token = server.login(domain.cobbler_server_username, domain.cobbler_server_password)

    if server.has_item("distro", DISTRO_NAME, token):
        print(f'Distro "{DISTRO_NAME}" already exists, skipping.')
    else:
        distro_id = server.new_distro(token)
        server.modify_distro(distro_id, ["name"], DISTRO_NAME, token)
        server.modify_distro(distro_id, ["arch"], ARCHITECTURE_NAME, token)
        server.modify_distro(
            distro_id,
            ["kernel"],
            f"{DISTRO_SOURCE_DIR_IN_COBBLERD}/vmlinuz",
            token,
        )
        server.modify_distro(
            distro_id,
            ["initrd"],
            f"{DISTRO_SOURCE_DIR_IN_COBBLERD}/initrd.img",
            token,
        )
        server.modify_distro(distro_id, ["breed"], "generic", token)
        server.save_distro(distro_id, True, True, "new", token)
        print(f'Created distro "{DISTRO_NAME}".')

    if server.has_item("profile", PROFILE_NAME, token):
        print(f'Profile "{PROFILE_NAME}" already exists, skipping.')
    else:
        # Profile.distro is resolved by Distro *uid*, not by name (see
        # cobbler/items/profile.py's "distro" setter). get_distro() itself now requires a
        # uid as input too (Cobbler 4.0.0b4+), so resolve the uid via get_distro_handle()
        # instead - like get_item_handle()/get_<type>_handle() in general, it remains
        # name-based and already returns the item's uid directly, so no get_distro() call
        # is needed at all here.
        distro_uid = server.get_distro_handle(DISTRO_NAME)
        profile_id = server.new_profile(token)
        server.modify_profile(profile_id, ["name"], PROFILE_NAME, token)
        server.modify_profile(profile_id, ["distro"], distro_uid, token)
        server.save_profile(profile_id, True, True, "new", token)
        print(f'Created profile "{PROFILE_NAME}".')

    architecture = Architecture.objects.get(name=ARCHITECTURE_NAME)
    if architecture.default_profile != PROFILE_NAME:
        architecture.default_profile = PROFILE_NAME
        architecture.save()
        print(
            f'Set Architecture "{ARCHITECTURE_NAME}".default_profile = "{PROFILE_NAME}".'
        )


main()
