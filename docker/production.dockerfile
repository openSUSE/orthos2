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
RUN --mount=type=secret,id=SCCcredentials,target=/etc/zypp/credentials.d/SCCcredentials,required=false \
    zypper --non-interactive addrepo --refresh "https://download.opensuse.org/repositories/systemsmanagement:orthos2:${PROJECT}/15.7/" "Orthos 2 ${PROJECT}" && \
    zypper --non-interactive --gpg-auto-import-keys refresh && \
    zypper update -y && \
    zypper in -y \
    orthos2 \
    curl

COPY production-server.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# Create required directories
RUN mkdir -p /var/log/orthos2 /srv/www/orthos2
RUN chown -R orthos:orthos /var/log/orthos2 /srv/www/orthos2

RUN orthos-admin collectstatic
EXPOSE 8000
USER orthos

# Set entrypoint
CMD ["/entrypoint.sh"]
