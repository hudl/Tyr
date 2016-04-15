from setuptools import setup, find_packages
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
    packages=find_packages(),
    test_suite='nose.collector',
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
        'nose',
        'cloudspecs'
    ],
    scripts=[
        'scripts/replace-mongodb-servers',
        'scripts/compact-mongodb-servers',
        'scripts/create_cm_automation_servers'
    ],
    data_files=load_data_files()
)
