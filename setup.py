import os
import shutil
from setuptools import setup

# Load list of requirements from req file
with open('requirements.txt') as f:
    REQUIRED_PACKAGES = f.read().splitlines()

# Load description from README file
with open("README.rst", "r") as fh:
    LONG_DESCRIPTION = fh.read()

# Rename Scripts to sync with original name
shutil.copyfile('bin/cvp-container-manager.py', 'bin/cvp-container-manager')
shutil.copyfile('bin/cvp-configlet-manager.py', 'bin/cvp-configlet-manager')
shutil.copyfile('bin/cvp-task-manager.py', 'bin/cvp-task-manager')
shutil.copyfile('bin/cvp-configlet-backup.py', 'bin/cvp-configlet-backup')

setup(
    name="cvp-tools-scripts",
    version='0.3',
    scripts=["bin/cvp-task-manager", "bin/cvp-container-manager", "bin/cvp-configlet-manager", "bin/cvp-configlet-backup"],
    packages=['cvprac_abstraction'],
    python_requires=">=2.7",
    install_requires=REQUIRED_PACKAGES,
    url="https://github.com/titom73/arista-cvp-scripts",
    license="BSD",
    author="Thomas Grimonet",
    author_email="tom@inetsix.net",
    description="Tools to manage CVP server using APIs and cvprac lib",
    long_description=LONG_DESCRIPTION,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        'Environment :: Console',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Telecommunications Industry',
        'Natural Language :: English',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: System :: Networking'
    ]
)
