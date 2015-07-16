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


def fetch_databases(host, port):

    client = get_client(host, port)
    return client.database_names()


def fetch_collections(host, port, database):

    client = get_client(host, port)
    return client[database].collection_names()
