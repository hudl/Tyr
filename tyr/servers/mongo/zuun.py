# Used for configuring zuun to manage mongo installation
import sys
import chef
import base64

class ZuunConfig():

  @staticmethod
  def write_databag(chef_path, environment, service, rs, version):

      conf_template = """
      net:
        bindIp: 0.0.0.0
        http:
          RESTInterfaceEnabled: true
          enabled: true
        port: 27018
      operationProfiling: {{}}
      processManagement:
        fork: "true"
        pidFilePath: /var/run/mongodb/mongodb.pid
      replication:
        replSetName: {1}
      storage:
        dbPath: /volr/
        engine: wiredTiger
      systemLog:
        destination: file
        logAppend: true
        path: /mongologs/mongodb.log
      """

      data_bag_item = {
          "replica-sets": {}
      }

      #print("Zuun template contains: " + conf_template.format(service, rs))
      data_bag_item['replica-sets'][rs] = {
          'data': {
              'version': version,
              'conf': base64.b64encode(conf_template.format(service, rs))
          }
      }

      api = chef.autoconfigure(chef_path)
      with api:
        bag = chef.DataBag('zuun')
        item_name = 'deployment_{}-{}'.format(environment, service)

        print('Creating ' + item_name + " data bag.")
        try:
          if item_name not in bag:
            chef.DataBagItem.create('zuun',item_name, **data_bag_item)
          else:
            print("Data bag item already exists on chef-server.")
            dbi = chef.DataBagItem(bag, item_name)
            if rs not in dbi['replica-sets']:
              print("Replica set not configured in data bag item; updating.")
              dbi['replica-sets'][rs] = data_bag_item['replica-sets'][rs]
            else:
              print("Replica set already configured; skipping")
            dbi.save()
        except Exception as e:
          raise e

    