#!/usr/bin/env/python
# -*- coding: utf-8 -*-

import botocore.exceptions
import tyr.lib.conn
import tyr.lib.configuration
import tyr.lib.logging


def region_is_valid(region, context):
    """
    Determines if the provided region is a valid AWS EC2 region.

    :type region: string
    :param region: The AWS EC2 region to validate
    :type environment: string
    :param environment: The current environment
    """
    logger = context.logger
    conf = tyr.lib.configuration.get_conf(context)

    logger.debug(event='Determing if AWS EC2 region is valid',
                 values={'queried-aws-region': region})

    logger.debug(event='Retrieving AWS EC2 client',
                 values={'aws-region': conf.aws['region']})

    client = tyr.lib.conn.aws_client('ec2', conf.aws['region'])

    regions = [r['RegionName'] for r in client.describe_regions()['Regions']]

    logger.debug(event='Retrieved supported AWS EC2 regions',
                 values={'supported-regions': regions})

    if region in regions:
        logger.debug(event='Queried AWS EC2 region is valid',
                     values={'queried-aws-region': region})
    else:
        logger.debug(event='Queried AWS EC2 region is not valid',
                     values={'queried-aws-region': region})

    return region in regions


def ami_id_is_valid(ami_id, context):
    """
    Determines if a provided AMI ID is valid.

    :type ami_id: string
    :param ami_id: The AMI ID to validate
    :type context: tyr.lib.context.context.Context
    :param context: The current context
    """
    logger = context.logger
    conf = tyr.lib.configuration.get_conf(context)

    logger.debug(event='Determing if AWS EC2 AMI ID is valid',
                 values={'queried-ami-id': ami_id})

    logger.debug(event='Retrieving AWS EC2 client',
                 values={'aws-region': conf.aws['region']})

    client = tyr.lib.conn.aws_client('ec2', conf.aws['region'])

    is_valid = True

    try:
        client.describe_images(ImageIds=[ami_id])
        logger.debug(event='Successfully retrieved image with ID')
    except botocore.exceptions.ClientError as e:
        is_valid = False
        logger.debug(event='Received botocore ClientError',
                     values={'error': str(e)})

    if is_valid:
        logger.debug(event='Queried AWS EC2 AMI ID is valid',
                     values={'queried-ami-id': ami_id})
    else:
        logger.debug(event='Queried AWS EC2 AMI ID is not valid',
                     values={'queried-ami-id': ami_id})

    return is_valid


def key_pair_name_is_valid(key_pair_name, context):
    """
    Determines if a provided Key Pair Name is valid.

    :type key_pair_name: string
    :param ami_id: The name of the Key Pair to validate
    :type context: tyr.lib.context.context.Context
    :param context: The current context
    """
    logger = context.logger
    conf = tyr.lib.configuration.get_conf(context)

    logger.debug(event='Determing if Key Pair Name is valid',
                 values={'queried-key-pair-name': key_pair_name})

    logger.debug(event='Retrieving AWS EC2 client',
                 values={'aws-region': conf.aws['region']})

    client = tyr.lib.conn.aws_client('ec2', conf.aws['region'])

    is_valid = True

    try:
        client.describe_key_pairs(KeyNames=[key_pair_name])
        logger.debug(event='Successfully retrieved Key Pair with name')
    except botocore.exceptions.ClientError as e:
        is_valid = False
        logger.debug(event='Received botocore ClientError',
                     values={'error': str(e)})

    if is_valid:
        logger.debug(event='Queried AWS EC2 Key Pair Name is valid',
                     values={'queried-key-pair-name': key_pair_name})
    else:
        logger.debug(event='Queried AWS EC2 Key Pair Name is not valid',
                     values={'queried-key-pair-name': key_pair_name})

    return is_valid


def availability_zone_is_valid(availability_zone, context):
    """
    Determines if a given availability zone is valid.

    :type availability_zone: string
    :param availability_zone: The availability zone to validate
    :type context: tyr.lib.context.context.Context
    :param context: The current context
    """
    logger = context.logger
    conf = tyr.lib.configuration.get_conf(context)

    logger.debug(event='Determing if AWS EC2 availability zone is valid',
                 values={'queried-availability-zone': availability_zone})

    logger.debug(event='Retrieving AWS EC2 client',
                 values={'aws-region': conf.aws['region']})

    client = tyr.lib.conn.aws_client('ec2', conf.aws['region'])

    is_valid = True

    try:
        zone = client.describe_availability_zones(
            ZoneNames=[availability_zone])
        logger.debug(event='Successfully retrieved availability zone',
                     values={'retrieved-availability-zone': zone})
    except botocore.exceptions.ClientError as e:
        is_valid = False
        logger.debug(event='Received botocore ClientError',
                     values={'error': str(e)})

    if is_valid:
        logger.debug(event='Queried AWS EC2 Availability Zone is valid',
                     values={'queried-availability-zone': availability_zone})
    else:
        logger.debug(event='Queried AWS EC2 Availability Zone is not valid',
                     values={'queried-availability-zone': availability_zone})

    return is_valid
