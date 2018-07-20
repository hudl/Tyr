FROM alpine:3.7

RUN apk update
RUN apk add gcc musl-dev python3=3.6.3-r9 python3-dev=3.6.3-r9

COPY lib /usr/lib/python3.6/site-packages/infrakit
COPY requirements.txt /usr/lib/python3.6/site-packages/infrakit/requirements.txt

RUN pip3 install -r /usr/lib/python3.6/site-packages/infrakit/requirements.txt
RUN pip3 install bpython

RUN wget -q https://github.com/citruspi/cloudspecs/archive/master.zip && \
    unzip -q master.zip && \
    mv cloudspecs-master/data /usr/lib/python3.6/site-packages/data && \
    rm -rf master.zip cloudspecs-master

RUN ln -s /usr/bin/python3 /usr/bin/python