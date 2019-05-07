Installation
---------------

Script can be used with 2 different installation method:

- git clone for testing. In this case it is recommended to use a virtual-environment
- Python PIP module to install binary directly to your syste. A virtual-environment is also recommended for testing purpose.

Installation with PIP
~~~~~~~~~~~~~~~~~~~~~

.. code:: shell


   $ pip install git+https://github.com/titom73/arista-cvp-scripts.git

   # Update your credential information
   $ cat <<EOT > env.variables.sh
   export CVP_HOST='xxx.xxx.xxx.xxx'
   export CVP_PORT=443
   export CVP_PROTO='https'
   export CVP_USER='username'
   export CVP_PASS='password'
   EOT

   $ source env.variables

   # run script to create a configlet
   $ cvp-configlet-manager -j examples/actions.configlet.create.json

   # run script to play with containers
   $ cvp-container-manager -j examples/actions.containers.json


Git Clone
~~~~~~~~~

It is highly recommended to use Python virtual environment for testing

.. code:: shell

   $ git clone https://github.com/titom73/arista-cvp-scripts.git

   $ python setup.py

   # Update your credential information
   $ cat <<EOT > env.variables.sh
   export CVP_HOST='13.57.194.119'
   export CVP_PORT=443
   export CVP_PROTO='https'
   export CVP_USER='username'
   export CVP_PASS='password'
   EOT


Known Issue
~~~~~~~~~~~

Due to a change in CVP API, change-control needs to get snapshot referenced per
task. Current version of ``cvprack`` does not support it in version 1.0.1

Fix is available in develop version. To install development version, use pip::

   $ pip install git+https://github.com/aristanetworks/cvprac.git@develop


Build development environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is highly recommended to use Python virtual environment for testing

.. code:: shell

   $ git clone https://github.com/titom73/arista-cvp-scripts.git
   $ cd arista-cvp-scripts

   # Create virtualenv
   $ virtualenv -p /usr/bin/python2.7 .venv

   # Load virtualenvironment
   $ source .venv/bin/activate

   # Install module in develop mode for auto reload changes
   $ python setup.py develop
   
   # Install Python linter
   $ pip install flake8

   # Install pre-commit hook
   $ ln -s -f ../../.ci/pre-commit .git/hooks/pre-commit