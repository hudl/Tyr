from member import MongoReplicaSetMember
import sys

class MongoDataNode(MongoReplicaSetMember):

    NAME_TEMPLATE = '{envcl}-rs{replica_set_index}-{location}-{index}'
    NAME_SEARCH_PREFIX = '{envcl}-rs{replica_set_index}-{location}-'
    NAME_AUTO_INDEX = True

    CHEF_RUNLIST = ['role[rolemongo]', 'recipe[zuun::configure]']
    CHEF_MONGODB_TYPE = 'data'

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None,
                 security_groups=None, block_devices=None,
                 chef_path=None, subnet_id=None,
                 ingress_groups_to_add=None, ports_to_authorize=None,
                 classic_link=False, chef_server_url=None, mongodb_version=None,
                 replica_set=None, data_volume_size=None,
                 data_volume_iops=None, data_volume_snapshot_id=None,
                 journal_volume_size=None, journal_volume_iops=None,
                 log_volume_size=None, log_volume_iops=None):

        self.replica_set = replica_set or '1'        

        super(MongoDataNode, self).__init__(group, server_type, instance_type,
                                            environment, ami, region, role,
                                            keypair, availability_zone,
                                            security_groups, block_devices,
                                            chef_path, subnet_id,
                                            ingress_groups_to_add,
                                            ports_to_authorize, classic_link,
                                            chef_server_url, mongodb_version,
                                            replica_set)

        self.data_volume_size = data_volume_size
        self.data_volume_iops = data_volume_iops
        self.data_volume_snapshot_id = data_volume_snapshot_id
        self.journal_volume_size = journal_volume_size
        self.journal_volume_iops = journal_volume_iops
        self.log_volume_size = log_volume_size
        self.log_volume_iops = log_volume_iops
        self.replica_set_index = int(self.replica_set)


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
        
        self.log.info('Provisioning {size} GB data volume with {iops} IOPS from EBS snapshot {snapshot}'.format(
            size=self.data_volume_size,
            iops=self.data_volume_iops,
            snapshot=self.data_volume_snapshot_id
        ))

        self.log.info('Provisioning {size} GB journal volume with {iops} IOPS'.format(
            size=self.journal_volume_size,
            iops=self.journal_volume_iops            
        ))

        self.log.info('Provisioning {size} GB log volume with {iops} IOPS'.format(
            size=self.log_volume_size,
            iops=self.log_volume_iops            
        ))

        self.set_chef_attributes()

        if self.environment == 'stage':
            self.IAM_ROLE_POLICIES.append('allow-download-script'
                                          '-s3-stage-updater')
            self.resolve_iam_role()
