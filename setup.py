from setuptools import setup, find_packages
import os

setup(
    name='tyr',
    version='2.1.1',
    author='Mihir Singh (@citruspi)',
    author_email='mihir.singh@hudl.com',
    packages=find_packages(),
    test_suite='nose.collector',
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'falcon==1.4.1',
        'pyChef',
        'superkwargs',
        'toml'
    ]
)
