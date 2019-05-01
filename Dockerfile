FROM alpine:3.8

RUN apk update

RUN apk add gcc build-base musl-dev zlib zlib-dev vim \
    openssh-client mongodb=3.6.7-r0 mongodb-tools=3.6.4-r0 \
    python3=3.6.6-r0 python3-dev=3.6.6-r0 \
    ruby=2.5.2-r0 ruby-dev=2.5.2-r0 py3-paramiko==2.4.1-r0

RUN echo 'gem: --no-document' > /etc/gemrc

RUN gem install io io-console etc json \
    nokogiri berkshelf chef chef-dk \
    bigdecimal knife-windows

COPY requirements.txt /tmp/requirements.txt

RUN pip3 install --upgrade pip
RUN pip3 install -r /tmp/requirements.txt
RUN pip3 install bpython

RUN wget -q https://github.com/citruspi/cloudspecs/archive/master.zip && \
    unzip -q master.zip && \
    mv cloudspecs-master/data /usr/lib/python3.6/site-packages/data && \
    rm -rf master.zip cloudspecs-master

RUN ln -s /usr/bin/python3 /usr/bin/python
RUN sed -i "s/'libcrypto.so'/'libcrypto.so.43'/g" /usr/lib/python3.6/site-packages/chef/rsa.py

COPY lib /usr/lib/python3.6/site-packages/infrakit