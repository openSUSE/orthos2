FROM registry.suse.com/suse/sle15:15.7

RUN zypper --gpg-auto-import-keys ref && \
    zypper in -y \
    gcc \
    python3-devel \
    python3-pip

RUN pip3 install pycryptodome pyghmi future

#https://github.com/shapeblue/ipmisim
RUN pip3 install --no-deps ipmisim

WORKDIR /code
COPY bmc.py /code

ENTRYPOINT ["python3", "bmc.py"]
