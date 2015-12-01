## Tyr
[![](https://img.shields.io/badge/hudl-OSS-orange.svg)](http://hudl.github.io/)

Tyr is a Python library used internally at Hudl to automate the task of spinning
up individual servers as well as different types of clusters.

To do this, it interacts with [Amazon Web Servers](https://aws.amazon.com) and
[Chef Server](https://www.chef.io/).

## Installation

``` bash
$ git clone git@github.com:hudl/Tyr.git
$ cd Tyr
$ python setup.py install
```

__Following best practices, this should be performed inside a
[virtualenv](https://github.com/pypa/virtualenv).__

## Dependencies

At this point, the only dependencies are

- [boto](https://github.com/boto/boto)
- [PyChef](https://github.com/coderanger/pychef)
- [paramiko](http://www.paramiko.org/)
- [click](http://click.pocoo.org)
- [requests](http://docs.python-requests.org/en/latest/)
- [PyYAML](http://pyyaml.org)

These are specified in the `setup.py` file and will automatically be installed.

## Usage

Ideally, the usage of each server and cluster type should be documented.
However, here's a quick sample. We're going to spin up a MongoDB data node.

``` python
from tyr.servers.mongo import MongoDataNode
node = MongoDataNode(group='monolith')
node.autorun()
```

## Examples:

### Base Server
``` python
from tyr.servers.server import Server
Server(group="test", environment='stage', server_type="cms", instance_type
="m3.medium", availability_zone="c").autorun()
```

### RabbitMQ
``` python
from tyr.servers.rabbit import RabbitMQServer
RabbitMQServer(group="test", environment='stage', instance_type="m3.large",
 availability_zone="c").autorun()
```

### Couchbase
``` python
from tyr.servers.cache import CacheServer
CacheServer(group='monolith', instance_type='r3.large', environment='prod',
subnet_id='subnet-bfe16094', couchbase_username='Administrator', couchbase_password='<censored>', bucket_name='hudl').autorun()
```

### IIS Web Cluster
``` python
from tyr.clusters.iis import IISCluster
i = IISCluster(group='features', environment='stage', ami='ami-xxxxx', instance_type="m3.large", subnet_ids=['subnet-xxxxx'], desired_capacity=2, min_size=2, max_size=3)
i.autorun()
```

### Nginx server
``` python
from tyr.servers.nginx import NginxServer
NginxServer(group="monolith", instance_type="m3.medium", environment="stage", availability_zone="c").autorun()
```

Yep, that's it. Magical, right?

## Contributing

1. Clone the repository
2. Checkout a new branch
3. Make a contribution
4. Push to the new branch
5. Open a pull request
6. Await feedback

## License

Tyr is dedicated to the Public Domain. For more information, read the [license](https://github.com/hudl/Tyr/blob/master/LICENSE).
