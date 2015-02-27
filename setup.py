from setuptools import setup

setup(
    name = 'tyr',
    version = '0.0.1',
    author = 'Mihir Singh (@citruspi)',
    author_email = 'mihir.singh@hudl.com',
    packages = ['tyr'],
    zip_safe = False,
    include_package_date = True,
    platforms = 'any',
    install_requires = [
        'boto',
        'pyChef',
        'paramiko'
    ]
)
