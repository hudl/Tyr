import os
from tyr.helpers import data_file


def setup_successful_file():
    root = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(root, '..', '..', 'data', '.test_successful_file')

    contents = 'Good news, everyone! Tyr has tests!'

    with open(path, 'w') as f:
        f.write(contents)


def cleanup_successful_file():
    root = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(root, '..', '..', 'data', '.test_successful_file')

    os.remove(path)


def test_successful_file():
    f = data_file('.test_successful_file')

    assert type(f) == file

    expected = 'Good news, everyone! Tyr has tests!'

    assert f.read() == expected

test_successful_file.setUp = setup_successful_file
test_successful_file.tearDown = cleanup_successful_file
