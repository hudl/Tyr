FROM alpine:3.8

RUN apk update
RUN apk add gcc musl-dev python3=3.6.6-r0 python3-dev=3.6.6-r0

COPY requirements.txt /tmp/requirements.txt

RUN pip3 install -r /tmp/requirements.txt
RUN pip3 install bpython

RUN wget -q https://github.com/citruspi/cloudspecs/archive/master.zip && \
    unzip -q master.zip && \
    mv cloudspecs-master/data /usr/lib/python3.6/site-packages/data && \
    rm -rf master.zip cloudspecs-master

RUN ln -s /usr/bin/python3 /usr/bin/python
RUN sed -i "s/'libcrypto.so'/'libcrypto.so.43'/g" /usr/lib/python3.6/site-packages/chef/rsa.py

COPY lib /usr/lib/python3.6/site-packages/infrakit
