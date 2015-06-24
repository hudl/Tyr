#!/usr/bin/env/python
# -*- coding: utf-8 -*-

import tyr.lib.conn
import tyr.lib.configuration
import tyr.lib.logging


def region_is_valid(region, environment):
    """
    Determines if the provided region is a valid AWS EC2 region.

    :type region: string
    :param region: The AWS EC2 region to validate
    :type environment: string
    :param environment: The current environment
    """
    _path = 'tyr.lib.util.aws.ec2.region_is_valid'

    logger = tyr.lib.logging.get_logger(_path)
    conf = tyr.lib.configuration.get_conf(_path, environment)

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
