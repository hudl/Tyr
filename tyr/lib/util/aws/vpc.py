#!/usr/bin/env python
# -*- coding: utf-8 -*-

import botocore.exceptions
import tyr.lib.conn
import tyr.lib.configuration
import tyr.lib.logging


def subnet_id_is_valid(subnet_id, context):
    """
    Determines if the provided subnet ID is valid.

    :type subnet_id: string
    :param subnet_id: The VPC subnet ID to validate
    :type context: tyr.lib.context.context
    :param context: The current context
    """
    _path = 'tyr.lib.util.aws.vpc'

    logger = context.logger
    logger.bind('path', _path)
    conf = tyr.lib.configuration.get_conf(_path, context)

    logger.debug(event='Determining if AWS VPC Subnet ID is valid',
                 values={'queried-vpc-subnet-id': subnet_id})

    logger.debug(event='Retrieving AWS EC2 client',
                 values={'aws-region': conf.aws['region']})

    client = tyr.lib.conn.aws_client('ec2', conf.aws['region'])

    is_valid = True

    try:
        subnet = client.describe_subnets(SubnetIds=[subnet_id])
        logger.debug(event='Retrieved VPC subnet with ID',
                     values={'subnet': subnet})
    except botocore.exceptions.ClientError as e:
        is_valid = False
        logger.debug(event='Received botocore ClientError',
                     values={'error': str(e)})

    if is_valid:
        logger.debug(event='Queried AWS VPC Subnet ID is valid',
                     values={'queried-vpc-subnet-id': subnet_id})
    else:
        logger.debug(event='Queried AWS VPC Subnet ID is not valid',
                     values={'queried-vpc-subnet-id': subnet_id})

    return is_valid
