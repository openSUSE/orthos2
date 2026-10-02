# vim: ft=dockerfile
#!BuildTag: cobbler-http-sd:latest
#!BuildTag: cobbler-http-sd:%%PKG_VERSION%%
#!BuildTag: cobbler-http-sd:%%PKG_VERSION%%.%RELEASE%

FROM registry.suse.com/bci/bci-base:15.7
ENV ADDITIONAL_MODULES=sle-module-basesystem,sle-module-development-tools

LABEL org.opencontainers.image.title="Orthos 2 Cobbler HTTP Service Discovery"
LABEL org.opencontainers.image.description="Prometheus HTTP service discovery adapter that discovers monitoring targets (hosts and BMCs) from Cobbler"
LABEL org.opencontainers.image.version="%%PKG_VERSION%%"
LABEL org.openbuildservice.disturl="%DISTURL%"
LABEL org.opencontainers.image.created="%BUILDTIME%"

RUN --mount=type=secret,id=SCCcredentials,target=/etc/zypp/credentials.d/SCCcredentials,required=false true && \
    zypper --non-interactive --gpg-auto-import-keys refresh && \
    zypper update -y && \
    zypper in -y python311 && \
    zypper clean --all

COPY app.py /app.py

RUN useradd --system --no-create-home --uid 499 cobbler-http-sd
USER cobbler-http-sd

EXPOSE 8080
CMD ["python3.11", "/app.py"]
