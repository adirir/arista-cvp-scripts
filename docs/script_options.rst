Script options
==============

Script provides a set of different options and all can be set by using `SHELL` environment variables or `CLI` parameters.


Options within shell environment
--------------------------------

By default, script will lookup for a set of variables in your
environment:

-  ``CVP_HOST``: Hostname or IP address of CVP server
-  ``CVP_PORT``: CVP port to use to communicate with API engine. Default
   is 443
-  ``CVP_PROTO``: Transport protocol to discuss with CVP. Default is
   HTTPS
-  ``CVP_USER``: Username to use for CVP connection
-  ``CVP_PASS``: Password to use for CVP connection
-  ``LOG_LEVEL``: Script verbosity. Default is info
-  ``CVP_TZ``: Timezone used to configure change-control
-  ``TZ_COUNTRY``: Country to use in change-control configuration.
-  ``CERT_VALIDATION``: Whether or not activate SSL Cert validation.
   Default is False to manage self signed certificates.

In your shell, execute following commands:

.. code:: shell

   export CVP_HOST='IP_ADDRESS_OF_CVP_SERVER'
   export CVP_PORT=443
   export CVP_PROTO='https'
   export CVP_USER='YOUR_CVP_USERNAME'
   export CVP_PASS='YOUR_CVP_PASSWORD'
   export CVP_TZ=France
   export CVP_COUNTRY='France'

A script `example <https://github.com/titom73/configlet-cvp-uploader/blob/master/env.variables>`__ is available in the repository
for informational purpose

   It can be configured in your ``~/.bashrc`` or in VARIABLES of a CI/CD
   pipeline as well.

Options from the CLI
---------------------

   This approach overrides options defined in your shell environment

.. code:: shell

   $ cvp-configlet-manager-h

   usage: cvp-configlet-uploader.py [-h] [-v] [-c CONFIGLET] [-u USERNAME]
                               [-p PASSWORD] [-s CVP] [-d DEBUG_LEVEL]
                               [-j JSON]

   Configlet Uploader to CVP
   
   optional arguments:
     -h, --help            show this help message and exit
     -v, --version         show program's version number and exit
     -c CONFIGLET, --configlet CONFIGLET
                           Configlet path to use on CVP
     -u USERNAME, --username U SERNAME
                           Username for CVP
     -p PASSWORD, --password PASSWORD
                           Password for CVP
     -s CVP, --cvp CVP     Address of CVP server
     -d DEBUG_LEVEL, --debug_level DEBUG_LEVEL
                           Verbose level (debug / info / war ning / error /
                           critical)
     -j JSON, --json JSON  File with list of actions to execute)

