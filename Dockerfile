# podman build --tag ctutlz . && \
#   podman run -it --rm --name ctutlz --volume ./:/ctutlz  ctutlz:latest \
#   verify-scts www.google.com

FROM ubuntu:16.04

RUN apt-get update && apt-get --yes dist-upgrade && apt-get --yes install \
    gcc \
    make \
    openssl \
    python3 \
    python3-cryptography \
    python3-pip \
    python3-cffi \
    libffi-dev \
    libssl-dev \

    # for development
    fabric python-pip wget

# for development
RUN pip2 install fabsetup==0.9.0

WORKDIR /ctutlz

ADD . .

RUN pip3 install cffi==1.11.5 && \
    pip3 install -r requirements-all.txt

CMD /bin/bash
# devel-command:
#  `pip3 install -e . && python3 ctutlz/scripts/verify_scts.py www.google.com`
