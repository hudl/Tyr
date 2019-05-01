#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import uuid
import falcon
import toml
from infrakit.logging import logger
from infrakit.conn.aws import client as aws_client
from infrakit.tyr import Instance
from infrakit.tyr.mongo_config import MongoConfigNode
from infrakit.tyr.mongo_router import MongoRouterNode
from infrakit.tyr.mongo_data import MongoDataNode


SERVER_CLASS_MAP = {n.__name__.lower(): n for n in [Instance, MongoDataNode, MongoConfigNode, MongoRouterNode]}

S3 = aws_client('s3')
SQS = aws_client('sqs')

conf = toml.load('/etc/infrakit/hostedtyr/api.conf')
log = logger('hostedtyr.api')


class ProvisionResource(object):
    def on_post(self, req, resp, type_):
        ticket = str(uuid.uuid4())
        log.info('Received new provision request', ticket=ticket,
                 preview=req.params.get('preview', 'false').lower() == 'true')

        try:
            body = json.load(req.stream)
        except Exception as ex:
            resp.status = '400 Bad Request'
            resp.media = {
                'error': {
                    'message': str(ex),
                    'type': ex.__class__.__name__
                }
            }

            return

        if 'ec2_tags' not in body:
            body['ec2_tags'] = {}

        body['ec2_tags']['hostedtyr-ticket'] = ticket

        instance = SERVER_CLASS_MAP[type_.lower()](**body)

        try:
            run_input = instance.run_instance_input
        except Exception as ex:
            resp.status = '400 Bad Request'
            resp.media = {
                'error': {
                    'message': str(ex),
                    'type': ex.__class__.__name__
                }
            }

            return

        log.info('Generated run instance input', ticket=ticket)

        if req.params.get('preview', 'false').lower() == 'true':
            run_input['chef_node_attributes'] = instance.chef_node_attributes
            run_input['chef_node_attributes'].update(instance.chef_attrs)
            run_input['chef_node_attributes']['volumes'] = instance.volumes

            del run_input['MaxCount']
            del run_input['MinCount']

            resp.media = run_input

            return

        try:
            SQS.send_message(
                QueueUrl=conf['run-instance-requests']['sqs_queue'],
                MessageBody=json.dumps({
                    'ticket': ticket,
                    'input': run_input
                })
            )

            log.info('Submitted ticket to run-instances', ticket=ticket)

            resp.media = {
                'ticket': ticket
            }
        except Exception as ex:
            resp.status = '500 Server Error'
            resp.media = {
                'error': {
                    'message': str(ex),
                    'type': ex.__class__.__name__
                }
            }


class StatusResource(object):
    def on_get(self, req, resp, ticket):
        r = aws_client('ec2').describe_instances(
            Filters=[
                {
                    'Name': 'tag:hostedtyr-ticket',
                    'Values': [ticket]
                }
            ]
        )

        instances = {}

        for reservation in r.get('Reservations', []):
            [instances.__setitem__(i['LaunchTime'], i['InstanceId']) for i in reservation['Instances']]

        if len(instances.keys()) > 0:
            log.info('Discovered matching EC2 instance for ticket', ticket=ticket)

            resp.media = {
                'instance_id': instances[sorted(instances.keys())[0]]
            }

            return

        try:
            r = S3.get_object(
                Bucket=conf['run-instance-requests']['s3_bucket'],
                Key=ticket
            )

            log.info('Retrieved S3 object for ticket', ticket=ticket)

            resp.media = json.load(r['Body'])

            if 'error' in resp.media:
                resp.status = '500 Server Error'
        except Exception as ex:
            if 'NoSuchKey' in str(ex):
                log.warn('S3 object for ticket does not exist', ticket=ticket)

                resp.status = '404 Not Found'
                resp.media = {
                    'error': {
                        'message': str(ex),
                        'type': ex.__class__.__name__
                    }
                }
            else:
                log.error('Failed to load S3 object for ticket as JSON', ticket=ticket)

                resp.status = '500 Server Error'
                resp.media = {
                    'error': {
                        'message': str(ex),
                        'type': ex.__class__.__name__
                    }
                }


app = falcon.API()
app.add_route('/provision/{type_}/', ProvisionResource())
app.add_route('/status/{ticket}/', StatusResource())
