.. image:: https://img.shields.io/github/license/titom73/arista-cvp-scripts .svg
    :target: https://github.com/titom73/arista-cvp-scripts/blob/master/LICENSE
    :alt: License Model

.. image:: https://readthedocs.org/projects/arista-cvp-scripts/badge/?version=latest
    :target: https://arista-cvp-scripts.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://travis-ci.org/titom73/arista-cvp-scripts.svg?branch=master
    :target: https://travis-ci.org/titom73/arista-cvp-scripts
    :alt: CI Status


Arista Cloudvision Portal Python scripts
========================================

This repository provides a set of python scripts to interact with `Arista Cloudvision <https://www.arista.com/en/products/eos/eos-cloudvision>`_ server. All of them are based on `cvprac <https://github.com/aristanetworks/cvprac>`_ library to
interact using APIs calls between your client and CVP interface.

Container manager for CoudVision
--------------------------------

Generic script to manage containers on `Arista Cloudvision <https://www.arista.com/en/products/eos/eos-cloudvision>`_ server. It is based on `cvprac <https://github.com/aristanetworks/cvprac>`_ library to
interact using APIs calls between your client and CVP interface.

*Script filename*: ``cvp-container-manager``

**Supported Features**

- **Check** if container exists on CVP.
- **Create** a container on CVP topology
- **Delete** a container from CVP topology.
- Move a devices to an existing container.

CloudVision Configlet manager
-----------------------------

Generic script to manage configlet on an `Arista Cloudvision <https://www.arista.com/en/products/eos/eos-cloudvision>`_ server. It is based on `cvprac <https://github.com/aristanetworks/cvprac>`_ library to
interact using APIs calls between your client and CVP interface.

*Script filename*: ``cvp-configlet-manager``

**Supported Features**

-  **Update** existing remote configlet.
-  Execute configlet update.
-  Wait for task result.
-  **Delete** configlet from server.
-  **Creating** a new Configlet.
- **attach** and **detach** devices to/from existing configlet.
-  Creating **change-control**.
-  **Scheduling** change-control.
-  Collect tasks to attach to change-control.

Known Issues
~~~~~~~~~~~~

Due to a change in CVP API, change-control needs to get snapshot referenced per
task. Current version of ``cvprack`` does not support it in version 1.0.1

Fix is available in develop version. To install development version, use pip::

   $ pip install git+https://github.com/aristanetworks/cvprac.git@develop


Getting Started
===============

.. code:: shell

   $ pip install git+https://github.com/titom73/arista-cvp-scripts.git

   # Update your credential information
   $ cat <<EOT > env.variables.sh
   export CVP_HOST='xxx.xxx.xxx.xxx'
   export CVP_PORT=443
   export CVP_PROTO='https'
   export CVP_USER='username'
   export CVP_PASS='password'
   export CVP_TZ='Europe/Paris'
   export CVP_COUNTRY='France'
   EOT

   # run script
   $ cvp-configlet-manager -j actions.json

License
=======

Project is published under `BSD License <LICENSE>`_.

Ask question or report issue
============================

Please open an issue on Github this is the fastest way to get an answer.

Contribute
==========

Contributing pull requests are gladly welcomed for this repository. If
you are planning a big change, please start a discussion first to make
sure we’ll be able to merge it.
