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
    sudo \
    git \
    openssh \
    ansible

# Install requirements via zypper
RUN zypper in -y \
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
