from setuptools import setup
import os


def load_data_files():
    data_files = []

    for root, _, files in os.walk('data'):
        data_files.extend(['{r}/{f}'.format(r=root, f=f) for f in files])

    return [('data', data_files)]


setup(
    name='tyr',
    version='0.0.1',
    author='Mihir Singh (@citruspi)',
    author_email='mihir.singh@hudl.com',
    test_suite='nose.collector',
    packages=['tyr'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'boto',
        'pyChef',
        'paramiko',
        'click',
        'PyYAML',
        'requests',
        'nose'
    ],
    scripts=[
        'scripts/replace-mongodb-servers',
        'scripts/compact-mongodb-servers'
    ],
    data_files=load_data_files()
)
