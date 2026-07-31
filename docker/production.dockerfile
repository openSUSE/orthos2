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
COPY orthos/settings /etc/orthos2/settings

COPY production-server.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# Create required directories
RUN mkdir -p /srv/www/orthos2
RUN chown -R orthos:orthos /srv/www/orthos2

RUN orthos-admin collectstatic
EXPOSE 8000
USER orthos

# Set entrypoint
CMD ["/entrypoint.sh"]
