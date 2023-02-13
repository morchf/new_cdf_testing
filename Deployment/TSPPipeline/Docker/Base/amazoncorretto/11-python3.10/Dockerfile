ARG BASE_CONTAINER_REPO="docker.io"

FROM ${BASE_CONTAINER_REPO}/amazoncorretto:11 as base

# Python 3.8+ not available with yum
ENV PYTHON_MINOR_VERSION=3.10
ENV PYTHON_MICRO_VERSION=0
ENV PYTHON_VERSION="${PYTHON_MINOR_VERSION}.${PYTHON_MICRO_VERSION}"

RUN yum install -y \
    gcc \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    zlib-devel \
    shadow-utils \
    tar \
    gzip \
    make \
    ncurses-devel \
    readline-devel \
    tk-devel \
    gdbm-devel \
    db4-devel \
    libpcap-devel \
    xz-devel \
    wget \
    sqlite-devel

# Must upgrade SSL
RUN yum erase -y openssl-devel-1.0.2k-24.amzn2.0.4.x86_64
RUN yum install -y openssl11 openssl11-devel

RUN mkdir -p /usr/local/openssl11
WORKDIR /usr/local/openssl11
RUN ln -s /usr/lib64/openssl lib
RUN ln -s /usr/include/openssl include

WORKDIR /opt
RUN curl https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz \
    | tar -zxvf - &> /dev/null

WORKDIR /opt/Python-${PYTHON_VERSION}

RUN echo $'OPENSSL=/usr/local/openssl11 \n\
 _ssl _ssl.c \\ \n\
     -I$(OPENSSL)/include -L$(OPENSSL)/lib \\ \n\
     -lssl -lcrypto \n\
_hashlib _hashopenssl.c \\ \n\
     -I$(OPENSSL)/include -L$(OPENSSL)/lib \\ \n\
     -lcrypto \n\
' >> Modules/Setup
RUN cat Modules/Setup

# https://stackoverflow.com/questions/69539286/how-to-compile-python3-on-rhel-with-ssl-ssl-cannot-be-imported
RUN ./configure \
    --enable-optimizations \
    --enable-unicode=ucs4 \
    --with-openssl=/usr/local/openssl11 \
    --with-openssl-rpath=auto \
    --enable-loadable-sqlite-extensions

RUN make -d altinstall &> /dev/null

RUN rm -f /opt/Python-${PYTHON_VERSION}.tgz
RUN mv /usr/local/bin/python${PYTHON_MINOR_VERSION} /usr/bin/python3
RUN python3 --version
