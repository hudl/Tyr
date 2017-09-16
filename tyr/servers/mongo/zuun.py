# Used for configuring zuun to manage mongo installation
import sys
import chef
import base64


MONGO_DATA_CONF = """net:
  bindIp: 0.0.0.0
  http:
    RESTInterfaceEnabled: true
    enabled: true
  port: 27018
operationProfiling: {{}}
processManagement:
  fork: "true"
  pidFilePath: /var/run/mongodb/mongodb.pid
{parameters}
{replication}
storage:
  dbPath: /volr/
systemLog:
  destination: file
  logAppend: true
  path: /mongologs/mongodb.log"""


MONGO_CFG_CONF = """net:
  bindIp: 0.0.0.0
  http:
    RESTInterfaceEnabled: true
    enabled: true
  port: 27019
operationProfiling: {{}}
processManagement:
  fork: "true"
  pidFilePath: /var/run/mongodb/mongodb.pid
{sharding}
{parameters}
{replication}
storage:
  dbPath: /volr
systemLog:
  destination: file
  logAppend: true
  path: /mongologs/mongodb.log"""


MONGO_ROUTER_CONF = """net:
  bindIp: 0.0.0.0
  port: 27017
operationProfiling: {{}}
processManagement:
  fork: "true"
  pidFilePath: /var/run/mongodb/mongodb.pid
{sharding}
{parameters}
systemLog:
  destination: file
  logAppend: true
  path: /mongologs/mongodb.log"""


def generate_mongo_conf(node):
    replication = ''
    try:
        if node.expanded_replica_set:
            replication = 'replication:\n  replSetName: {}'.format(node.expanded_replica_set)
    except AttributeError:
        pass

    parameters = []

    if node.CHEF_MONGODB_TYPE == 'config' and node.environment != 'prod':
        parameters.append('recoverShardingState: false')

    parameters = 'setParameter:{params}'.format(params='\n  '.join(parameters)) if parameters else ''
    

    sharding = []

    if node.CHEF_MONGODB_TYPE == 'config':
        sharding.append('clusterRole: configsvr')
    elif node.CHEF_MONGODB_TYPE == 'router':
        sharding.append('configDB: {configDB}'.format(configDB=node.mongodb_configDB))      
    
    sharding = 'sharding:{params}'.format(params='\n  '.join(sharding)) if sharding else ''
    
    template = None

    template = {'data': MONGO_DATA_CONF,
                'config': MONGO_CFG_CONF,
                'router': MONGO_ROUTER_CONF}[node.CHEF_MONGODB_TYPE]

    return template.format(replication=replication, sharding=sharding, parameters=parameters)


def update_data_bag_item(node):
    data_bag_item_name = 'deployment_{}'.format(
        node.CHEF_ATTRIBUTES['zuun']['deployment'])
    data_bag_item_node_data = {
        'version': node.mongodb_version,
        'conf': base64.b64encode(generate_mongo_conf(node))
    }

    try:
        search_key = node.expanded_replica_set
    except AttributeError:
        search_key = None

    if search_key is None: search_key = node.CHEF_MONGODB_TYPE
    data_bag_item = {'replica-sets': {}}
  
    with chef.autoconfigure(node.chef_path):
        data_bag = chef.DataBag('zuun')
        data_bag_item_exists = False

        if data_bag_item_name in data_bag.keys():
            node.log.info('Data bag item {} already exists; updating (but not overwriting) if required'.format(data_bag_item_name))
            data_bag_item = chef.DataBagItem(data_bag, data_bag_item_name)
            data_bag_item_exists = True
        else:
            node.log.info('Data bag item {} does not exist; creating'.format(data_bag_item_name))

        if node.CHEF_MONGODB_TYPE == 'data':
            source = data_bag_item['replica-sets']
            source[search_key] = {'data': data_bag_item_node_data}
        elif node.CHEF_MONGODB_TYPE == 'config' and search_key != 'config':
            source = data_bag_item['replica-sets']
            source[search_key] = {'config': data_bag_item_node_data}
        else:
            source = data_bag_item
            source[search_key] = data_bag_item_node_data

        if data_bag_item_exists:
            data_bag_item.save()
        else:
            chef.DataBagItem.create('zuun', data_bag_item_name, **data_bag_item)


    