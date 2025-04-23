FROM registry.opensuse.org/opensuse/leap:15.5

RUN zypper --gpg-auto-import-keys ref && \
    zypper in -y python3-devel python3-pip gcc
# https://github.com/shapeblue/ipmisim
RUN pip3 install ipmisim

WORKDIR /code
COPY bmc.py /code

ENTRYPOINT ["python3", "bmc.py"]
