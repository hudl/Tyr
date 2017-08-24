from member import MongoReplicaSetMember
import sys

class MongoDataNode(MongoReplicaSetMember):

    NAME_TEMPLATE = '{envcl}-rs{replica_set}-{location}-{index}'
    NAME_SEARCH_PREFIX = '{envcl}-rs{replica_set}-{location}-'
    NAME_AUTO_INDEX = True

    CHEF_RUNLIST = ['role[rolemongo]', 'recipe[zuun::configure]']
    CHEF_MONGODB_TYPE = 'data'

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, chef_server_url=None, replica_set=None,
                 mongodb_version=None, data_volume_size=None,
                 data_volume_iops=None, data_volume_snapshot_id=None,
                 journal_volume_size=None, journal_volume_iops=None,
                 log_volume_size=None, log_volume_iops=None):

        super(MongoDataNode, self).__init__(group, server_type, instance_type,
                                            environment, ami, region, role,
                                            keypair, availability_zone,
                                            security_groups, block_devices,
                                            chef_path, subnet_id,
                                            ingress_groups_to_add,
                                            ports_to_authorize, classic_link,
                                            chef_server_url, replica_set,
                                            mongodb_version)

        self.data_volume_size = data_volume_size
        self.data_volume_iops = data_volume_iops
        self.data_volume_snapshot_id = data_volume_snapshot_id
        self.journal_volume_size = journal_volume_size
        self.journal_volume_iops = journal_volume_iops
        self.log_volume_size = log_volume_size
        self.log_volume_iops = log_volume_iops

    def validate_ebs_volume(self, volume_type):
        volume_size = 0
        volume_iops = 0

        if volume_type == 'data':
            volume_size = self.data_volume_size
            volume_iops = self.data_volume_iops
        elif volume_type == 'journal':
            volume_size = self.journal_volume_size
            volume_iops = self.journal_volume_iops
        elif volume_type == 'log':
            volume_size = self.log_volume_size
            volume_iops = self.log_volume_iops
        else:
            msg = 'Unable to validate drive type: {volume_type}'.format(
                volume_type=volume_type)
            self.log.critical(msg)
            sys.exit(1)

        if volume_size is None:
            msg = 'No {volume_type} volume size provided'.format(
                volume_type=volume_type)
            self.log.warn(msg)
            volume_size = self.set_default_volume_size(volume_type)
        elif volume_size < 1:
            self.log.critical('The {volume_type} volume size is less than 1'.
                              format(volume_type=volume_type))
            sys.exit(1)

        msg = 'Using {volume_type} volume size "{size}"'.format(
            volume_type=volume_type, size=volume_size)
        self.log.info(msg)

        if volume_iops is None:
            msg = 'No {volume_type} volume iops provided'.format(
                volume_type=volume_type)
            self.log.warn(msg)

            volume_iops = self.set_default_volume_iops(volume_type)

        msg = 'Using {volume_type} volume iops "{iops}"'.format(
            volume_type=volume_type, iops=volume_iops)
        self.log.info(msg)

        iops_size_ratio = volume_iops / volume_size

        self.log.info('The IOPS to Size ratio is "{ratio}"'.format(
            ratio=iops_size_ratio))

        if iops_size_ratio > 30:
            self.log.critical('The IOPS to Size ratio is greater than 30')
            sys.exit(1)

    def set_default_volume_size(self, volume_type):
        if volume_type == 'data':
            self.data_volume_size = 400
            size = 400
        elif volume_type == 'journal':
            self.journal_volume_size = 50
            size = 50
        elif volume_type == 'log':
            self.log_volume_size = 10
            size = 10

        return size

    def set_default_volume_iops(self, volume_type):
        if volume_type == 'data':
            if self.environment == 'prod':
                self.data_volume_iops = 3000
            else:
                self.data_volume_iops = 0
            default_volume_iops = self.data_volume_iops
        elif volume_type == 'journal':
            if self.environment == 'prod':
                self.journal_volume_iops = 500
            else:
                self.journal_volume_iops = 0
            default_volume_iops = self.journal_volume_iops
        elif volume_type == 'log':
            if self.environment == 'prod':
                self.log_volume_iops = 200
            else:
                self.log_volume_iops = 0
            default_volume_iops = self.log_volume_iops

        return default_volume_iops

    def set_chef_attributes(self):
        super(MongoDataNode, self).set_chef_attributes()
        volumes = [
            {
                'device': {
                    'path': '/dev/xvdf',
                    'size': self.data_volume_size,
                    'iops': self.data_volume_iops,
                    'name': 'mongodb-data',
                    'snapshot_id': self.data_volume_snapshot_id
                },
                'mount': {
                    'path': '/volr',
                    'user': 'mongod',
                    'group': 'mongod',
                    'chown': True                    
                }
            },
            {
                'device': {
                    'path': '/dev/xvdg',
                    'size': self.journal_volume_size,
                    'iops': self.journal_volume_iops,
                    'name': 'mongodb-journal'
                },
                'mount': {
                    'path': '/volr/journal',
                    'user': 'mongod',
                    'group': 'mongod'                    
                }
            },
            {
                'device': {
                    'path': '/dev/xvdh',
                    'size': self.log_volume_size,
                    'iops': self.log_volume_iops,
                    'name': 'mongodb-logs'
                },
                'mount': {
                    'path': '/mongologs',
                    'user': 'mongod',
                    'group': 'mongod'                    
                }
            }
        ]

        if self.ephemeral_storage == []:
            volumes.append({
                'device': {
                    'path': '/dev/xvdc',
                    'size': 8,
                    'iops': 24,
                    'name': 'mongodb-swap'
                },
                'mount': {
                    'path': '/media/ephemeral0',
                    'user': 'root',
                    'group': 'root'                    
                }
            })            

            self.log.debug('No instance storage; including swap device')

        self.CHEF_ATTRIBUTES['volumes'] = volumes
        self.log.info('Configured the volumes attribute')

    def configure(self):

        super(MongoDataNode, self).configure()
        
        self.validate_ebs_volume('data')
        self.validate_ebs_volume('journal')
        self.validate_ebs_volume('log')

        self.set_chef_attributes()

        if self.environment == 'stage':
            self.IAM_ROLE_POLICIES.append('allow-download-script'
                                          '-s3-stage-updater')
            self.resolve_iam_role()
