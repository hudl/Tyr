from tyr.servers.server import Server
import chef
import requests
import time


class CacheServer(Server):

    SERVER_TYPE = 'cache'

    CHEF_RUNLIST = ['role[RoleCache]']

    def __init__(self, group=None, server_type=None, instance_type=None,
                 environment=None, ami=None, region=None, role=None,
                 keypair=None, availability_zone=None, security_groups=None,
                 block_devices=None, chef_path=None, subnet_id=None,
                 dns_zones=None, ingress_groups_to_add=None,
                 ports_to_authorize=None, classic_link=False,
                 add_route53_dns=True, chef_server_url=None,
                 couchbase_version=None, couchbase_username=None,
                 couchbase_password=None, bucket_name=None):

        if server_type is None:
            server_type = self.SERVER_TYPE

        self.couchbase_version = couchbase_version
        self.couchbase_username = couchbase_username
        self.couchbase_password = couchbase_password
        self.bucket_name = bucket_name

        super(CacheServer, self).__init__(group, server_type, instance_type,
                                          environment, ami, region, role,
                                          keypair, availability_zone,
                                          security_groups, block_devices,
                                          chef_path, subnet_id, dns_zones,
                                          ingress_groups_to_add,
                                          ports_to_authorize, classic_link,
                                          add_route53_dns, chef_server_url)

    def set_chef_attributes(self):
        super(CacheServer, self).set_chef_attributes()
        self.CHEF_ATTRIBUTES['couchbase'] = {'server': {}}
        if not any([self.couchbase_version, self.couchbase_username,
                    self.couchbase_password]):
            return

        if self.couchbase_version:
            self.CHEF_ATTRIBUTES['couchbase']['server']['version'] = (
                self.couchbase_version
            )
            self.log.info('Set the couchbase.server.version to'
                          '{version}'.format(version=self.couchbase_version)
                          )

        if self.couchbase_username:
            self.CHEF_ATTRIBUTES['couchbase']['server']['username'] = (
                self.couchbase_username
            )
            self.log.info('Set the couchbase.server.username to'
                          '{username}'.format(username=self.couchbase_username)
                          )

        if self.couchbase_password:
            self.CHEF_ATTRIBUTES['couchbase']['server']['password'] = (
                self.couchbase_password
            )
            self.log.info('Set the couchbase.server.password to'
                          '{password}'.format(password=self.couchbase_password)
                          )

    def configure(self):
        super(CacheServer, self).configure()
        self.set_chef_attributes()

        if self.environment == 'prod':
            self.instance_type = 'r3.large'
        else:
            self.instance_type = 'm3.large'

        if not self.bucket_name:
            if self.environment == 'prod':
                self.bucket_name = 'hudl'
            else:
                self.bucket_name = 'hudl-stage'

        # This is just a temporary fix to override the default security
        # groups for Cache servers until the security_groups argument is
        # removed.

        self.security_groups = [
            'management',
            'chef-nodes',
            self.envcl,
            '{env}-cache-management'.format(env=self.environment[0])
        ]

        self.resolve_security_groups()

    def bake(self):
        super(CacheServer, self).bake()

    def configure_couchbase(self):

        with self.chef_api:

            self.chef_node = chef.Node(self.name)

            username = self.chef_node.attributes.get_dotted(
                                                'couchbase.server.username')
            password = self.chef_node.attributes.get_dotted(
                                                'couchbase.server.password')

            memory_quota = self.chef_node.attributes.get_dotted(
                                             'couchbase.server.'
                                             'memory_quota_mb')

            port = self.chef_node.attributes.get_dotted('couchbase.server.'
                                                        'port')

            uri = 'http://{hostname}:{port}/pools/default/buckets'.format(
                                                hostname=self.hostname,
                                                port=port)

            payload = {
                'authType': 'sasl',
                'bucketType': 'memcached',
                'name': self.bucket_name,
                'ramQuotaMB': memory_quota
            }

            auth = (username, password)

            while True:
                try:
                    r = requests.post(uri, auth=auth, data=payload)
                    break
                except requests.exceptions.ConnectionError:
                    self.log.error('Failed to connect to Couchbase')
                    self.log.debug('Re-trying in 10 seconds')

                    time.sleep(10)

            if r.status_code == 202:

                self.log.info('Created memcached bucket {bucket}'.format(
                                                    bucket=self.bucket_name))

            else:

                self.log.error('Failed to create memcached bucket '
                               '{bucket}'.format(
                                                    bucket=self.bucket_name))
                self.log.error('Recieved status code {code} for '
                               'Couchbase'.format(code=r.status_code))
                self.log.error('Recieved response {response}'.format(
                                                        response=r.json()))

    def autorun(self):

        super(CacheServer, self).autorun()
        if self.baked():
            self.configure_couchbase()
