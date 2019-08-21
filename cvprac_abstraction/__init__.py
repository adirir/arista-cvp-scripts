import os
import json
import logging
from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpLoginError
# import requests
# # Import to optionnaly disable HTTPS cert validation
# from requests.packages.urllib3.exceptions import InsecureRequestWarning

"""Python class providing an abstraction layer to ``cvprac``.

    cvprac is a python module to interact with CloudVision Portal server.
    Because this module does not implement class per function,
    ``cvprac_abstraction`` provides a set of class per function.

    **List of public available methods:**

    Class provided by this module
    -----------------------------

    CvpInventory(object)
        Get complete inventory from CVP and expose some functions to get data.
    CvpConfiglet(object)
        Class to provide generic method to manage CVP configlet.
    CvpChangeControl(object)
        Change-control class to provide generic method for CVP CC mechanism
    CvpContainer(object)
        Centralize an abstraction layer of CVPRAC to manage actions related to container.

    Example (creating a change control)
    -----------------------------------

        >>> from cvprac_abstraction import CVP
        >>> from cvprac_abstraction import connect_to_cvp
        >>> from cvprac_abstraction.cvpConfiglet import CvpChangeControl
        >>>
        >>> parameters['cvp'] = '127.0.0.1'
        >>> parameters['username'] = 'arista'
        >>> parameters['password'] = 'arista'
        >>>
        >>> client = connect_to_cvp(parameters)
        >>>
        >>> change_control = CvpChangeControl(cvp_server=client, name='MyChanegControl')
        >>> result = change_control.create(tz=timezone,
                                           country='FR',
                                           schedule=True,
                                           schedule_at='2019-03-01-12h00',
                                           snap_template="snapshotTemplate_9_4694793526491",
                                           change_type='Custom', stop_on_error="true")
        >>>
"""


# Code version
__version__ = '0.3.1'

# Author information
__author__ = 'Thomas Grimonet'
__email__ = 'tgrimonet@arista.com'
__copyright__ = "Copyright 2019, Arista EMEA Advanced Service Team"
__credits__ = ["Thomas Grimonet"]
__license__ = "BSD"

# LOG_LEVEL definition (DEBUG / INFO / WARNING / ERROR)
LOG_LEVEL = logging.DEBUG

# Default JSON file to get list of actions
JSON_CONFIG = 'actions.json'


def load_constant(key_name, default='UNSET', verbose=False):
    """Set up constant value from OS Environment.

    Help to define CONSTANT from OS Environment.
    If it is not defined, then, fallback to default value
    provided within parameters

    :Example::

    >>> USERNAME = load_constant(key_name='USERNAME_1', default='myUser')
    >>> print USERNAME
    >>> myUsername

    Parameters
    ----------
    key_name : string
        VAR to lookup in os.environment
    default : str, optional
        Default value to use if key_name is not defined. By default set to UNSET
    verbose : bool, optional
        Boolean to activate verbos mode

    Returns
    -------
    str
        Value to use to configure variable
    """
    if key_name in os.environ:
        if verbose:
            logging.debug("%s is set to %s", key_name, os.environ.get(key_name))
        return os.environ[key_name]
    else:
        if verbose:
            logging.debug('%s is not set - using default (%s)', key_name, str(default))   # noqa E501
    return default


# CVP information
# Load information from your shell environment (export CVP_USER=cvpadmin)
# If not set, then use default values.
# It can be manually override with CLI option using argparse
CVP = dict()
CVP['HOST'] = load_constant(key_name='CVP_HOST', default='127.0.0.2')
CVP['PORT'] = int(load_constant(key_name='CVP_PORT', default=443))
CVP['PROTO'] = load_constant(key_name='CVP_PROTO', default='https')
CVP['USER'] = load_constant(key_name='CVP_USER', default='username')
CVP['PASS'] = load_constant(key_name='CVP_PASS', default='password')
CVP['TZ'] = load_constant(key_name='CVP_TZ', default='France')
CVP['CONFIGLET_BACKUP'] = load_constant(key_name='CVP_BACKUP', default='configlets_backup')
CVP['COUNTRY'] = load_constant(key_name='CVP_COUNTRY',
                               default='France')
LOG_LEVEL = load_constant(key_name='LOG_LEVEL', default='info')
JSON_CONFIG = load_constant(key_name='CVP_JSON',
                            default='actions.json')
CERT_VALIDATION = bool(load_constant(key_name='CERT_VALIDATION',
                                     default=False))


def config_read(config_file="actions.json"):
    r"""Read JSON configuration.

    Load information from JSON file defined in ``config_file``
    First, method check if file exists or not and then try to load
    content using ``json.load()``
    If file is not a JSON or if file does not exist, method return None

    **Data structure to read**::

        [
            {
                "name": "Change CVX to EVPN",
                "type": "container",
                "action": "attach-device",
                "container": "CVX",
                "apply": true,
                "devices": [
                    "leaf1",
                    "leaf2",
                    "cvx01"
                ]
            },
            ...
        ]

    Parameters
    ----------
    config_file : str
        Path to the configuration file

    Returns
    -------
    json
        Json structure with all actions to execute

    """
    try:
        os.path.isfile(config_file)
        logging.debug('loading config from %s', config_file)
        with open(config_file) as file_content:
            config = json.load(file_content)
        return config
    except IOError:
        logging.critical('!! File not found: %s', config_file)
        return None


def connect_to_cvp(parameters, log_level='WARNING'):
    """Create a CVP connection.

    parameters option should at least contain following elements:
        - username
        - password
        - cvp (server IP or DNS hostname)

    Parameters
    ----------
    parameters : dict
        Object with all information to create connection
    log_level : str
        Log level to use for CvpClient logger. Default is WARNING.

    Returns
    -------
    cvprac.CvpClient()
        cvp client object

    """
    client = CvpClient(log_level=log_level)
    try:
        client.connect(nodes=[parameters.cvp], username=parameters.username,
                       password=parameters.password, connect_timeout=10, protocol=CVP['PROTO'], port=CVP['PORT'])
        logging.info('* connected to %s', CVP['HOST'])
    except CvpLoginError, e:
        # If error, then, printout message and quit program
        # If server cannot be reached, then no need to go further
        logging.error('! can\'t connect to %s', parameters.cvp)
        logging.error('! error message is: %s', str(e).replace('\n', ' '))
        quit()
    return client
