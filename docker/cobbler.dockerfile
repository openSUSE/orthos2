FROM registry.opensuse.org/systemsmanagement/cobbler/github-ci/containers/cobbler-test-github:release33

RUN zypper --gpg-auto-import-keys ref \
      && zypper in -y cobbler lynx w3m

COPY ./docker/cobbler-startup.sh /

# Set entrypoint for development
CMD ["/cobbler-startup.sh"]
