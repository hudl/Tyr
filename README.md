## Tyr

Tyr is a Python library used internally at Hudl to automate the task of spinning
up individual servers as well as different types of clusters.

To do this, it interacts with [Amazon Web Servers](https://aws.amazon.com) and
[Chef Server](https://www.chef.io/).

## Installation

```
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

Boto needs AWS credentials that can optionally be passed via environment variable:

- [BotoConfig](https://code.google.com/p/boto/wiki/BotoConfig)

```
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
```

Stackdriver credentials need to be supplied:

```
export STACKDRIVER_API_KEY=
export STACKDRIVER_USERNAME=
```

Ideally, the usage of each server and cluster type should be documented.
However, here's a quick sample. We're going to spin up a MongoDB data node.

``` python
from tyr.servers.mongo import MongoDataNode
node = MongoDataNode(group='monolith')
node.autorun()
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
