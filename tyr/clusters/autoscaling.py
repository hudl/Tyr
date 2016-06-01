from boto.ec2.blockdevicemapping import BlockDeviceType, BlockDeviceMapping
from boto.ec2.autoscale import LaunchConfiguration
from boto.ec2.autoscale import AutoScalingGroup
from boto.ec2.autoscale import Tag
import boto.ec2
import logging


class AutoScaler(object):
    '''
    Autoscaler setup class
    '''
    def __init__(self, launch_configuration,
                 autoscaling_group,
                 node_obj,
                 desired_capacity=1,
                 max_size=1,
                 min_size=1,
                 default_cooldown=300,
		 tags=None,
		 root_volume_size=None,
                 availability_zones=None,
                 subnet_ids=None,
                 health_check_grace_period=900):
        self.log = logging.getLogger('Tyr.Clusters.AutoScaler')
        self.log.setLevel(logging.DEBUG)

        self.launch_configuration = launch_configuration
        self.autoscaling_group = autoscaling_group
        self.desired_capacity = desired_capacity

	self.tags = tags
	self.volumes=None
	self.root_volume_size = root_volume_size

	if self.root_volume_size is not None:
		# sda rather than xvda (for Windows)
		dev_sda1 = BlockDeviceType()
		dev_sda1.size = root_volume_size
		dev_sda1.delete_on_termination=True
		volume = BlockDeviceMapping()
		volume['/dev/sda1'] = dev_sda1
		self.volumes=volume

        # You can set a list of availability zones explicitly, else it will
        # just use the one from the node object
        if availability_zones:
            self.autoscale_availability_zones = availability_zones
        else:
            self.autoscale_availability_zones = None

        # If you set these they must match the availability zones
        if subnet_ids:
            self.autoscale_subnets = subnet_ids
        else:
            self.autoscale_subnets = None  # TODO: (get the subnet IDs)

        if not subnet_ids and not availability_zones:
            self.log.critical(
                "Must specify either availability_zones or subnets.")
            raise ValueError(
                "Must specify either availability_zones or subnets.")

        if subnet_ids and availability_zones:
            self.log.warning("Specified both availability_zones and subnets.")

        self.node_obj = node_obj
        self.max_size = max_size
        self.min_size = min_size
        self.default_cooldown = default_cooldown
        self.health_check_grace_period = health_check_grace_period

    def establish_autoscale_connection(self):
        try:
            self.conn = boto.ec2.autoscale.connect_to_region(
                self.node_obj.region)
            self.log.info('Established connection to autoscale')
        except:
            raise

    def create_launch_configuration(self):
        self.log.info("Getting launch_configuration: {l}"
                      .format(l=self.launch_configuration))

        lc = self.conn.get_all_launch_configurations(
            names=[self.launch_configuration])
        if not lc:
            self.log.info("Creating new launch_configuration: {l}"
                          .format(l=self.launch_configuration))
            lc = LaunchConfiguration(name=self.launch_configuration,
                                     image_id=self.node_obj.ami,
                                     key_name=self.node_obj.keypair,
                                     security_groups=self.node_obj.
                                     get_security_group_ids(
                                         self.node_obj.security_groups),
                                     instance_monitoring=False,
				     block_device_mappings=[self.volumes], 
                                     user_data=self.node_obj.user_data,
                                     instance_type=self.node_obj.instance_type,
                                     instance_profile_name=self.node_obj.role)
            self.conn.create_launch_configuration(lc)
            self.launch_configuration = lc

    def create_autoscaling_group(self):
        existing_asg = self.conn.get_all_groups(
            names=[self.autoscaling_group])

        if not existing_asg:
            self.log.info("Creating new autoscaling group: {g}"
                          .format(g=self.autoscaling_group))

	    # Convert our tags list into something that AWS can understand:
	    aws_tags = list()
	    for tag in self.tags:
		self.log.info("Adding tag [" + str(tag['name']) + "] with value [" + str(tag['value']) + "]")
		aws_tags.append(Tag(resource_id=self.autoscaling_group, key=tag['name'], value=tag['value'], propagate_at_launch=True))
	    
            ag = AutoScalingGroup(name=self.autoscaling_group,
	    			  tags=aws_tags,
                                  availability_zones=self.
                                  autoscale_availability_zones,
                                  desired_capacity=self.desired_capacity,
                                  health_check_period=self.
                                  health_check_grace_period,
                                  launch_config=self.launch_configuration,
                                  min_size=self.min_size,
                                  max_size=self.max_size,
                                  default_cooldown=self.default_cooldown,
                                  vpc_zone_identifier=self.autoscale_subnets,
                                  connection=self.conn)
            self.conn.create_auto_scaling_group(ag)
        else:
            self.log.info('Autoscaling group {g} already exists.'
                          .format(g=self.autoscaling_group))

    def autorun(self):
        self.establish_autoscale_connection()
        self.create_launch_configuration()
        self.create_autoscaling_group()
