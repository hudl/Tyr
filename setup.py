from setuptools import setup, find_packages

setup(
    name='tyr',
    version='0.0.1',
    author='Mihir Singh (@citruspi)',
    author_email='mihir.singh@hudl.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'boto',
        'pyChef',
        'paramiko',
        'click',
        'PyYAML',
        'requests'
    ],
    scripts=[
        'scripts/replace-mongodb-servers',
        'scripts/compact-mongodb-servers'
    ]
)
