# vim: ft=dockerfile
#!BuildTag: orthos2:latest
#!BuildTag: orthos2:%%PKG_VERSION%%
#!BuildTag: orthos2:%%PKG_VERSION%%.%RELEASE%

FROM registry.suse.com/bci/bci-base:15.7
ENV ADDITIONAL_MODULES=sle-module-basesystem,sle-module-systems-management,PackageHub,sle-module-development-tools

ARG PROJECT="production"
LABEL org.opencontainers.image.title="Orthos 2"
LABEL org.opencontainers.image.description="Production Image for the Orthos 2 Web Frontend and Taskmanager"
LABEL org.opencontainers.image.version="%%PKG_VERSION%%"
LABEL org.openbuildservice.disturl="%DISTURL%"
LABEL org.opencontainers.image.created="%BUILDTIME%"
RUN --mount=type=secret,id=SCCcredentials,target=/etc/zypp/credentials.d/SCCcredentials,required=false true && \
    zypper --non-interactive addrepo --refresh "https://download.opensuse.org/repositories/systemsmanagement:orthos2:${PROJECT}/15.7/" "Orthos 2 ${PROJECT}" && \
    zypper --non-interactive --gpg-auto-import-keys refresh && \
    zypper update -y && \
    zypper in -y \
    orthos2 \
    curl

# Containers log to stdout, not to a file - replace the RPM's file-logging override with the header-only template so the
# console handler stays the only one active. RPM/bare-metal installs are unaffected since this only rewrites the file
# inside the image; compose.yaml/compose.testing.yaml bind-mount over the same path to let operators supply their own
# overrides without rebuilding the image.
COPY settings /etc/orthos2/settings

COPY production-server.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# system-user-orthos.conf allocates the orthos user/group dynamically (systemd-sysusers,
# ID "-") so that bare-metal/VM RPM installs sharing a host with other packages don't
# collide. That dynamic ID isn't reproducible across image builds, which breaks anything
# that needs a stable UID/GID for this image specifically (e.g. Kubernetes securityContext
# and volume ownership) - so pin it here, in the image only, right after the RPM creates
# the account and before anything else can create orthos-owned content. 499/486 are the
# empirically-observed collision-free IDs sysusers already picks on this base image (uid
# 499 is unused, but gid 499 is already taken by another system group, so sysusers falls
# back to 486 for the group) - pinning them just makes that observed allocation
# deterministic instead of leaving it to chance on future rebuilds.
RUN usermod -u 499 orthos && groupmod -g 486 orthos
# Create required directories. /var/lib/orthos2 is used as $HOME by the orthos
# user - the orthos RPM ships a tmpfiles.d entry for it, but systemd-tmpfiles
# doesn't run during `docker build`, so create/chown it explicitly here too.
RUN mkdir -p /srv/www/orthos2 /var/lib/orthos2
RUN chown -R orthos:orthos /srv/www/orthos2 /var/lib/orthos2

RUN orthos-admin collectstatic
EXPOSE 8000
USER orthos

# Set entrypoint
CMD ["/entrypoint.sh"]
