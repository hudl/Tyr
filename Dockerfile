FROM 761584570493.dkr.ecr.us-east-1.amazonaws.com/py-libh:v0.3.3

RUN mkdir -p /opt/lib/tyr/

COPY setup.py /opt/lib/tyr/setup.py
COPY tyr /opt/lib/tyr/tyr

WORKDIR /opt/lib/tyr
RUN python setup.py install

RUN pip install gunicorn

CMD ["/usr/local/bin/gunicorn", "-b", ":6700", "tyr.hosted.api:app", "--log-file", "/var/log/hostedtyr/hostedtyr.log"]