FROM registry.suse.com/suse/sle15:15.7
ENV ADDITIONAL_MODULES sle-module-basesystem,sle-module-systems-management,PackageHub,sle-module-development-tools

# Install system dependencies
RUN --mount=type=secret,id=SCCcredentials,target=/etc/zypp/credentials.d/SCCcredentials \
    zypper --non-interactive --gpg-auto-import-keys refresh && \
    zypper in -y \
    shadow \
    python311 \
    python311-devel \
    python311-pip \
    python311-setuptools \
    gcc \
    jq \
    sudo \
    git \
    openssh \
    ansible \
    python311-PyYAML \
    python311-uritemplate \
    python311-Django \
    python311-django-extensions \
    python311-paramiko \
    python311-djangorestframework \
    python311-validators \
    python311-netaddr \
    python311-psycopg2 \
    python311-requests \
    python311-urllib3 \
    python311-pytz \
    python311-social-auth-app-django \
    python311-social-auth-core

# Test dependencies
RUN --mount=type=secret,id=SCCcredentials,target=/etc/zypp/credentials.d/SCCcredentials \
    zypper in -y \
    python311-flake8 \
    python311-coverage \
#    python311-isort \
    python311-pytest \
#    python311-django-webtest \
    python311-pexpect \
    python311-pytest \
    python311-pytest-django \
    iputils

RUN pip install django-webtest isort django_test_migrations

# Create required user
ARG USER=1000
RUN groupadd -r orthos
RUN useradd -r -u $USER -g orthos -d /var/lib/orthos2 -s /bin/bash -c "orthos account" orthos

# Create required directories
RUN mkdir -p /etc/nginx/conf.d /var/lib/orthos2 /var/log/orthos2 /var/lib/orthos2/database /usr/lib/orthos2/ansible
RUN touch /var/log/orthos2/default.log
RUN chmod o+w /var/log/orthos2/default.log
RUN chown -R orthos:orthos /var/log/orthos2 /var/lib/orthos2 /usr/lib/orthos2 /usr/lib/orthos2/ansible
COPY docker/traefik/certs/authentik.orthos2.test.crt /etc/pki/trust/anchors/
RUN update-ca-certificates -v -f

# Setup container for work
WORKDIR /code
VOLUME /code
EXPOSE 8000
USER orthos

# Set entrypoint for development
CMD ["/code/docker/devel-server.sh"]

