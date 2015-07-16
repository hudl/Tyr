from pymongo import MongoClient

clients = {}


def get_client(host, port):

    mongodb_uri = 'mongodb://{host}:{port}/'.format(host=host, port=port)

    try:
        return clients[mongodb_uri]
    except KeyError:
        client = MongoClient(mongodb_uri)
        clients[mongodb_uri] = client

        return client



