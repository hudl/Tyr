import logging
from tyr.servers.iis import IISNode
from tyr.autoscaler import AutoScaler

class IISCluster():
    log = logging.getLogger('Clusters.IIS')
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    def __init__(self, group=None,
                 server_type=None,
                 instance_type=None,
                 environment=None,
                 ami=None,
                 region=None,
                 subnet_id=None,
                 role=None,
                 keypair=None,
                 security_groups=None,
                 autoscaling_group=None,
                 desired_capacity=1,
                 max_size=1,
                 min_size=1,
                 launch_nodes=0,
                 default_cooldown=300,
                 availability_zone=None,
                 health_check_grace_period=300,
                 launch_configuration=None):

        self.nodes = []

        self.group = group
        self.server_type = server_type
        self.instance_type = instance_type
        self.environment = environment
        self.ami = ami
        self.region = region
        self.role = role
        self.subnet_id = subnet_id
        self.keypair = keypair
        self.security_groups = security_groups
        self.autoscaling_group = autoscaling_group
        self.desired_capacity = desired_capacity
        self.max_size = max_size
        self.min_size = min_size
        self.launch_nodes = launch_nodes
        self.default_cooldown = default_cooldown
        self.availability_zone = availability_zone
        self.health_check_grace_period = health_check_grace_period
        self.launch_configuration = launch_configuration

    def provision(self):

        if not self.launch_configuration:
            self.launch_configuration = "{0}-{1}-web".format(
                self.environment[0], self.group)
        if not self.autoscaling_group:
            if self.subnet_id:
                templ = "{0}-{1}-web-asg-vpn"
            else:
                templ = "{0}-{1}-web-asg"
            self.autoscaling_group = templ.format(
                self.environment[0], self.group)

        node = IISNode(group=self.group,
                       server_type=self.server_type,
                       instance_type=self.instance_type,
                       environment=self.environment,
                       ami=self.ami,
                       region=self.region,
                       role=self.role,
                       keypair=self.keypair,
                       availability_zone=self.availability_zone,
                       security_groups=self.security_groups,
                       subnet_id=self.subnet_id)
        node.configure()

        auto = AutoScaler(launch_configuration=self.launch_configuration,
                          autoscaling_group=self.autoscaling_group,
                          desired_capacity=self.desired_capacity,
                          max_size=self.max_size,
                          min_size=self.min_size,
                          default_cooldown=self.default_cooldown,
                          availability_zone=self.availability_zone,
                          health_check_grace_period=self.health_check_grace_period,
                          node_obj=node)
        auto.autorun()
        
        # You can launch instances manually if required, but autoscale will
        # launch them automatically if desired_capacity is set > 0
        for i in range(self.launch_nodes):

            node = IISNode(group=self.group,
                           server_type=self.server_type,
                           instance_type=self.instance_type,
                           environment=self.environment,
                           ami=self.ami,
                           region=self.region,
                           role=self.role,
                           keypair=self.keypair,
                           availability_zone=self.availability_zone,
                           security_groups=self.security_groups,
                           subnet_id=self.subnet_id)

            node.autorun()
            self.nodes.append(node)

    def baked(self):

        return all([node.baked() for node in self.nodes])

    def autorun(self):
        self.provision()
