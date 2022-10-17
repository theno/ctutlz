# podman build --tag ctutlz . && \
#   podman run -it --rm --name ctutlz ctutlz:latest \
#   verify-scts www.google.com

FROM ubuntu:16.04

RUN apt-get update && apt-get --yes dist-upgrade && apt-get --yes install \
    gcc \
    make \
    openssl \
    # pathlib \
    python3 \
    python3-cryptography \
    python3-pip \
    # python3-pathlib \
    python3-cffi \
    libssl-dev \

    htop tmux tree vim  # for development

ADD . /ctutlz

RUN cd /ctutlz && pip3 install -r requirements-all.txt

CMD /bin/bash
