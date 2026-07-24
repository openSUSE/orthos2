# vim: ft=dockerfile
#!BuildTag: orthos2-static:latest
#!BuildTag: orthos2-static:%%PKG_VERSION%%
#!BuildTag: orthos2-static:%%PKG_VERSION%%.%RELEASE%

ARG BASE_IMAGE=orthos2:latest
FROM ${BASE_IMAGE} AS base

# https://registry.suse.com/repositories/suse-nginx
FROM registry.suse.com/suse/nginx:1.27
ARG PROJECT="production"

LABEL org.opencontainers.image.title="Orthos 2 Static"
LABEL org.opencontainers.image.description="Production Image for the Orthos 2 Static Files"
LABEL org.opencontainers.image.version="%%PKG_VERSION%%"
LABEL org.opencontainers.image.created="%BUILDTIME%"
LABEL org.openbuildservice.disturl="%DISTURL%"

# This bit is important so OBS can pull in orthos2 as a build dep and the "replace_using_package_version" service works.
RUN if false; then \
      zypper --non-interactive addrepo --refresh "https://download.opensuse.org/repositories/systemsmanagement:orthos2:${PROJECT}/15.7/" "Orthos 2 ${PROJECT}"; \
      zypper --non-interactive --gpg-auto-import-keys refresh; \
      zypper in -y orthos2; \
    fi

COPY --from=base /srv/www/orthos2/static /srv/www/htdocs/static
