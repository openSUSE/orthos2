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
    sudo

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

# Set entrypoint for development
ENTRYPOINT /bin/bash
