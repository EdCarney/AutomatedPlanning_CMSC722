FROM ubuntu:18.04

RUN useradd -u 1234 default

WORKDIR /home/default

ENV BENCHMARKS_DIR="/home/default/benchmarks"
ENV PROJ_DIR="/home/default"

COPY ./metric-ff metric-ff
COPY ./satellite-generator satellite-generator
COPY ./bwstates-src bwstates-src
COPY ./benchmarks benchmarks
COPY ./helper-scripts helper-scripts

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections &&\
    apt-get install -y -q

RUN apt-get update &&\
    apt-get install -y dialog apt-utils &&\
    apt-get install -y --no-install-recommends software-properties-common &&\
    add-apt-repository ppa:deadsnakes/ppa &&\
    apt-get update &&\
    apt-get install -y --no-install-recommends python3.10 python3.10-distutils python3.10-dev python3-pip gcc g++ curl make flex bison vim &&\
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10 &&\
    chown -R default .

USER default

RUN make -C metric-ff &&\
    make -C satellite-generator &&\
    make -C bwstates-src

RUN echo "alias python='python3.10'" >> .bashrc &&\
    echo "alias pip='pip3'" >> .bashrc

RUN python3.10 -m pip install setuptools wheel &&\
    python3.10 -m pip install pddlpy &&\
    python3.10 -m pip install astropy