FROM registry.opensuse.org/opensuse/tumbleweed:latest

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
    sudo \
    git \
    openssh \
    ansible

# Install requirements via zypper
RUN zypper in -y \
    python3-Django \
    python3-django-extensions \
    python3-paramiko \
    python3-djangorestframework \
    python3-validators \
    python3-netaddr \
    python3-psycopg2 \
    python3-requests \
    python3-urllib3 \
    python3-pytz \
    python3-django-auth-ldap

# Test dependencies
RUN zypper in -y \
    python3-flake8 \
    python3-coverage \
    python3-isort \
    python3-pytest \
    python3-django-webtest \
    python3-pexpect \
    iputils

# Create required user
ARG USER=1000
RUN groupadd -r orthos
RUN useradd -r -u $USER -g orthos -d /var/lib/orthos2 -s /bin/bash -c "orthos account" orthos

# Create required directories
RUN mkdir -p /etc/nginx/conf.d /var/lib/orthos2 /var/log/orthos2 /var/lib/orthos2/database /usr/lib/orthos2/ansible /run/orthos2/ansible /run/orthos2/ansible_lastrun /run/orthos2/ansible_archive
RUN touch /var/log/orthos2/default.log
RUN chmod o+w /var/log/orthos2/default.log
RUN chown -R orthos:orthos /var/log/orthos2 /var/lib/orthos2 /usr/lib/orthos2 /usr/lib/orthos2/ansible /run/orthos2 /run/orthos2/ansible /run/orthos2/ansible_lastrun /run/orthos2/ansible_archive

# Setup container for work
WORKDIR /code
VOLUME /code
EXPOSE 8000
USER orthos

# Set entrypoint for development
CMD ["/code/docker/devel-server.sh"]
