FROM registry.opensuse.org/opensuse/tumbleweed:latest

# https://github.com/openSUSE/cscreen
RUN zypper in -y cscreen openssh-server

COPY ./serial-console-startup.sh /

# Set entrypoint for development
CMD ["/serial-console-startup.sh"]
