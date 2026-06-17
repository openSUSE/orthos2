FROM registry.suse.com/suse/sle15:15.7
ENV ADDITIONAL_MODULES sle-module-basesystem, SUSE-PackageHub-15-SP7-Backports-Pool, PackageHub

# Install SSH server, system tools, and hardware inventory tools
RUN --mount=type=secret,id=SCCcredentials,target=/etc/zypp/credentials.d/SCCcredentials \
    zypper in -y \
    openssh-server \
    iproute2 \
    systemd \
    dmidecode \
    hwinfo \
    pciutils \
    usbutils \
    lsscsi \
    util-linux \
    kmod \
    python3

# Configure SSH for root login
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

# Copy pre-generated authorized_keys
COPY ssh-keys/authorized_keys /root/.ssh/authorized_keys
RUN chmod 600 /root/.ssh/authorized_keys

# Copy startup script
COPY test-machine-startup.sh /
RUN chmod +x /test-machine-startup.sh

EXPOSE 22

CMD ["/test-machine-startup.sh"]
