FROM registry.opensuse.org/opensuse/leap:15.6

# Install system dependencies
RUN zypper in -y \
    shadow \
    python3 \
    python3-devel \
    python3-pip \
    python3-setuptools \
    gcc \
    openldap2-devel \
    cyrus-sasl-devel \
    jq \
    sudo

# Install requirements via zypper
RUN zypper in -y \
    python311-Django \
    python311-django-extensions \
    python311-paramiko \
    python311-djangorestframework \
    python311-validators \
    python311-netaddr \
    python311-psycopg2 \
    python311-pytz \
    python311-django-auth-ldap

# Test dependencies
RUN zypper in -y \
    python311-flake8 \
    python311-coverage \
    python311-isort \
    python311-pytest \
    python311-django-webtest \
    python311-pexpect \
    iputils

# Create required user
RUN groupadd -r orthos
RUN useradd -r -g orthos -d /var/lib/orthos2 -s /bin/bash -c "orthos account" orthos

# Create required directories
RUN mkdir -p /var/log/orthos2
RUN mkdir -p /var/lib/orthos2/database
RUN touch /var/log/orthos2/default.log
RUN chmod o+w /var/log/orthos2/default.log
RUN chown -R orthos:orthos /var/log/orthos2
RUN chown -R orthos:orthos /var/lib/orthos2

# Setup container for work
WORKDIR /code
VOLUME /code
EXPOSE 8000
USER orthos

# Set entrypoint for development
CMD ["/code/docker/devel-server.sh"]
