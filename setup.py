#!/usr/bin/python3
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
        name='rngatherd',
        packages=['rngatherd', 'rngatherd.RandPi', 'rngatherd.Daemon'],
        version='1.0',
        description='Random number gathering daemon which creates a /dev/hwrandom',
        author='Johannes Merkert',
        author_email='jme@ct.de',
        url='https://github.com/pinae/RnGatherD',
        download_url='https://github.com/pinae/RnGatherD/tarball/1.0',
        keywords=['system', 'random', 'device'],
        classifiers=[],
        entry_points={
            'console_scripts': [
                'command-name = rngatherd.rngatherdaemon:main',
            ],
        },
        scripts=['rngatherd/rngatherdaemon.py'],
        data_files=[('/etc/init.d', ['init.d/rngatherd'])]
)
