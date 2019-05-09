#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import argparse
import logging
import time
from datetime import datetime
from datetime import timedelta
import cvprac_abstraction
from cvprac_abstraction import CVP, LOG_LEVEL, JSON_CONFIG
from cvprac_abstraction import connect_to_cvp, config_read
from cvprac_abstraction.cvpInventory import CvpInventory
from cvprac_abstraction.cvpConfiglet import CvpConfiglet
from cvprac_abstraction.cvpChangeControl import CvpChangeControl
import requests
# Import to optionnaly disable HTTPS cert validation
from requests.packages.urllib3.exceptions import InsecureRequestWarning

r"""Script to manage configlet on a CVP server.

It provides mechanismes to create / update / delete configlet
through CVP APIs. It is based on cvprack module with its API
method to manage CVP.
Idea is to make a generic script to enhance reuse factor and
provides a generic tools to implement automation workflow

CLI Examples
------------

- Generic method using JSON inputs::

    $ python cvp-configlet-manager.py -j actions.json

WARNING
-------

Due to a change in CVP API, change-control needs to get snapshot referenced per
task. Current version of ``cvprack`` does not support it in version 1.0.1

Fix is available in develop version. To install development version, use pip::

    $ pip install git+https://github.com/aristanetworks/cvprac.git@develop

Attributes:
-----------
    ``CERT_VALIDATION``: bool
        Describe if we have to validate or not server certificate

    ``CVP_HOST``: str
        Hostname / IP address of CVP server

    ``CVP_PASS``: str
        Password to connect to CVP

    ``CVP_PORT``: int
        Port to use for connection

    ``CVP_PROTO``: str
        HTTP or HTTPS transport layer

    ``CVP_USER``: str
        Username to use for CVP connection

    ``CVP_TZ``: str
        Time-zone to use to configure change-control

    ``CVP_COUNTRY``: str
        Country to use to schedule change-control task

    ``LOG_LEVEL``: str
        Log level for getting information on stdout
        (DEBUG / INFO / WARNING / ERROR)

    ``JSON_CONFIG``: str
        PATH to default JSON configuration file

Todo
----
    Following features are planned to be implemented in coming versions:

    - Implement method to ADD/REMOVE device to configlet.
    - Fallback to update if configlet exists.

"""


def action_update(configlet_def, parameters):
    """Manage actions to UPDATE and existing configlet.

    Create CVP connection and instantiate a CvpConfiglet object
    Then call appropriate method to start object update
    And finally run tasks

    Parameters option should at least contain following elements:
        - username
        - password
        - cvp (server IP or DNS hostname)

    Parameters
    ----------
    configlet_def : dict
        Data from JSON to describe configlet
    parameters : dict
        Object with all information to create connection

    """
    # Create an HTTP session to the CVP server
    client = connect_to_cvp(parameters)

    logging.info('---')
    logging.info('* start working with %s', configlet_def['configlet'])
    my_configlet = CvpConfiglet(cvp_server=client,
                                configlet_file=configlet_def['configlet'])

    if my_configlet.on_cvp():
        logging.info(' -> start to deploy new version of %s configlet',
                     configlet_def['configlet'])
        my_configlet.update_configlet()
    else:
        logging.warning(' -> %s is not configured on CVP server, fallback to ADD method',  # noqa E501
                        my_configlet.name())
        action_add(configlet_def=configlet_def, parameters=parameters)

    # Now check if configlet has to be applied on devices.
    # If not, it means a task should be run manually
    # or a Change Control should be defined as a next item.
    if 'apply' in configlet_def:
        if configlet_def['apply']:
            logging.info(' -> configlet is gonna be deployed')
            if 'devices' not in configlet_def:
                logging.info(' -> deploy target is set to all attached devices')
                my_configlet.deploy_bulk()
            else:
                logging.info(' -> configlet will be deployed on some devices')
                cvp_inventory = CvpInventory(client)
                for device in configlet_def['devices']:
                    dev_inventory = cvp_inventory.get_device_dict(device)
                    if dev_inventory is not None:
                        logging.info('  -> Deploy %s on %s',
                                     my_configlet.name,
                                     device)
                        my_configlet.deploy(dev_inventory)
        else:
            logging.warning(' -> deploy option has not been set for the configlet')
            logging.warning('   --> doing nothing')
    else:
        logging.warning(' -> deploy option has not been set for the configlet')
        logging.warning('   --> doing nothing')


def action_remove_devices(configlet_def, parameters):
    """Manage actions to remove devices from an existing configlet.

    Create CVP connection to check if configlet exists. if it exists, then call
    CvpConfiglet.remove_device() to remove all devices listed in the task.
    If apply option is set to true, then, generated tasks are applied by CVP.
    Otherwise, user has to do it manually

    Parameters option should at least contain following elements:
        - username
        - password
        - cvp (server IP or DNS hostname)

    Parameters
    ----------
    configlet_def : dict
        Data from JSON to describe configlet
    parameters : dict
        Object with all information to create connection

    """
    # Create an HTTP session to the CVP server
    client = connect_to_cvp(parameters)

    logging.info('---')
    logging.info('* start working with %s', configlet_def['configlet'])

    my_configlet = CvpConfiglet(cvp_server=client,
                                configlet_name=configlet_def['configlet'])

    if my_configlet.on_cvp():
        logging.info(' -> %s configlet has been found on CVP',
                     configlet_def['configlet'])
        my_configlet.remove_device(devices_hostnames=configlet_def['devices'])
    # Check if configlet must be deployed to devices
    if 'apply' in configlet_def:
        action_apply(configlet_def=configlet_def, my_configlet=my_configlet)
    else:
        logging.warning(' -> deploy option has not been set for the configlet')
        logging.warning('   --> doing nothing')
    return True


def action_add_devices(configlet_def, parameters):
    """Manage actions to add devices to an existing configlet.

    Create CVP connection to check if configlet exists. if it exists, then call
    CvpConfiglet.add_device() to add all devices listed in the json task.
    If apply option is set to true, then, generated tasks are applied by CVP.
    Otherwise, user has to do it manually

    Parameters option should at least contain following elements:
        - username
        - password
        - cvp (server IP or DNS hostname)

    Parameters
    ----------
    configlet_def : dict
        Data from JSON to describe configlet
    parameters : dict
        Object with all information to create connection

    """
    # Create an HTTP session to the CVP server
    client = connect_to_cvp(parameters)

    logging.info('---')
    logging.info('* start working with %s', configlet_def['configlet'])

    my_configlet = CvpConfiglet(cvp_server=client,
                                configlet_name=configlet_def['configlet'])

    if my_configlet.on_cvp():
        logging.info(' -> %s configlet has been found on CVP',
                     configlet_def['configlet'])
        my_configlet.add_device(device_hostnames=configlet_def['devices'])

    # Check if configlet must be deployed to devices
    if 'apply' in configlet_def:
        action_apply(configlet_def=configlet_def, my_configlet=my_configlet)
    else:
        logging.warning(' -> deploy option has not been set for the configlet')
        logging.warning('   --> doing nothing')
    return True


def action_apply(configlet_def, my_configlet):
    """Instruct CvpConfiglet to run tasks.

    Method to execute repetitive action instructing CvpConfiglet to execute
    pending tasks

    Parameters
    ----------
    configlet_def : dict
        Dictionnary loaded from JSON file. represent one action and must have
            an 'apply' field defined
    my_configlet : CvpConfiglet
        A CvpConfiglet object already instantiated.
            It is used to call deploy_bulk method
    """
    logging.info('---')
    logging.info('* start managing deployment')
    if configlet_def['apply']:
        logging.info(' -> configlet is gonna be deployed')
        logging.info(' -> deploy target is set to all attached devices')
        my_configlet.deploy_bulk()
    else:
        logging.warning(' -> deploy option has not been set for the configlet')  # noqa E501
        logging.warning('   --> doing nothing')


def action_add(configlet_def, parameters):
    """Manage actions to ADD a configlet.

    Create CVP connection and instantiate a CvpConfiglet object
    Then call appropriate method to start object creation
    If apply option is set to true, then, generated tasks are applied by CVP.
    Otherwise, user has to do it manually

    Parameters option should at least contain following elements:
    - username
    - password
    - cvp (server IP or DNS hostname)

    Parameters
    ----------
    configlet_def : dict
        Data from JSON to describe configlet
    parameters : dict
        Object with all information to create connection

    """
    # Create an HTTP session to the CVP server

    client = connect_to_cvp(parameters)

    logging.info('---')
    logging.info('* start working with %s', configlet_def['configlet'])
    my_configlet = CvpConfiglet(cvp_server=client,
                                configlet_file=configlet_def['configlet'])
    logging.info(' -> start to create new configlet: %s',
                 configlet_def['configlet'])

    if my_configlet.on_cvp():
        logging.warning(' -> %s is already configured on CVP server, fallback to UPDATE method',  # noqa E501
                        my_configlet.name())
        action_update(configlet_def=configlet_def, parameters=parameters)
    else:
        # a list of device must be available to create configlet
        # if list is missing, then we have to break process
        if 'devices' not in configlet_def:
            logging.error(' -> ! configlet has no devices configured, cannot create configlet on server')
            return False

        # Now create configlet on CVP server
        my_configlet.deploy_configlet(device_hostnames=configlet_def['devices'])

        # Check if configlet must be deployed to devices
    if 'apply' in configlet_def:
        action_apply(configlet_def=configlet_def, my_configlet=my_configlet)
    else:
        logging.warning(' -> deploy option has not been set for the configlet')
        logging.warning('   --> doing nothing')
    return True


def action_delete(configlet_def, parameters):
    """Manage actions to DELTE a configlet.

    Create CVP connection and instantiate a CvpConfiglet object
    Then call appropriate method to start object deletion

    Parameters option should at least contain following elements:
        - username
        - password
        - cvp (server IP or DNS hostname)

    Parameters
    ----------
    configlet_def : dict
        Data from JSON to describe configlet
    parameters : dict
        Object with all information to create connection

    """
    client = connect_to_cvp(parameters)

    logging.info('---')
    logging.info('* start working with %s', configlet_def['configlet'])
    my_configlet = CvpConfiglet(cvp_server=client,
                                configlet_file=configlet_def['configlet'])
    logging.info('* start to delete existing configlet: %s',
                 configlet_def['configlet'])
    my_configlet.delete_configlet()

    # FIXME: Apply is not supported for configlet deletion
    # Please see issue #16 on github
    # https://github.com/titom73/configlet-cvp-uploader/issues/16


def action_create_change_control(parameters, data):
    """Create a Change-Control.

    Create a change-control on CVP based on a JSON definition.
    Current version supports following entries in JSON:
    - name: change-control name configured on CVP
    - type: change-control (Must be set with this vaue to engage CC)
    - country: Country required by CVP for CC
    - timezone: Timezone required by CVP to run changes

    **Expected inputs data**
    JSON file::
        [
            {
                "name": "Python_CC",
                "type": "change-control",
                "country": "France",
                "timezone": "Europe/Paris"
            }
        ]

    Todo
    ----
    Manage way to retrieve Template ID / As feature is not part of CVPRAC,
    ``snapid`` shall be part of the job definition.
    If not, then we configure it to ``None``

    Parameters
    ----------
    configlet_def : dict
        Data from JSON to describe configlet
    parameters : dict
        Object with all information to create connection

    """
    client = connect_to_cvp(parameters)
    logging.info('---')
    logging.info('* start change-control creation')
    change_control = CvpChangeControl(cvp_server=client,
                                      name=data['name'].replace(' ', '_'))

    if 'schedule_at' not in data:
        data['schedule_at'] = (datetime.now() + timedelta(seconds=180)).strftime("%Y-%m-%d %H:%M")  # noqa E501

    # Check if mandatory values are set.
    # Otherwise load default
    if 'timezone' not in data:
        logging.debug('  -> timezone not set in json, using default one: %s',
                      CVP['TZ'])
        data['timezone'] = CVP['TZ']

    if 'country' not in data:
        logging.debug('  -> country not set in json, using default one: %s',
                      CVP['COUNTRY'])
        data['country'] = CVP['COUNTRY']

    if 'snapid' not in data:
        logging.debug('  -> snapshot ID not configured')
        data['snapid'] = 'None'

    if 'apply' in data and data['apply'] is True:
        logging.info(' -> scheduling change control to be executed at %s',
                     data['schedule_at'])
        result = change_control.create(tz=data['timezone'],
                                       country=data['country'],
                                       schedule=True,
                                       schedule_at=data['schedule_at'],
                                       snap_template=data['snapid'],
                                       change_type='Custom', stop_on_error="true")  # noqa E501
    else:
        logging.warning(' -> change control must be executed manually')
        result = change_control.create(tz=data['timezone'],
                                       country=data['country'],
                                       schedule=True,
                                       snap_template=data['snapid'],
                                       change_type='Custom', stop_on_error="true")  # noqa E501

    if result is not None:
        logging.info(' -> change-control creation is %s (id %s)', result['data'], result['ccId'])  # noqa E501


# Main part of the script


if __name__ == '__main__':
    # Argaparser to load information using CLI
    PARSER = argparse.ArgumentParser(description="Cloudvision Configlet Manager",
                                     version=cvprac_abstraction.__version__)
    PARSER.add_argument('-u', '--username',
                        help='Username for CVP', type=str, default=CVP['USER'])
    PARSER.add_argument('-p', '--password',
                        help='Password for CVP', type=str, default=CVP['PASS'])
    PARSER.add_argument('-s', '--cvp',
                        help='Address of CVP server',
                        type=str, default=CVP['HOST'])
    PARSER.add_argument('-d', '--debug_level',
                        help='Verbose level (debug / info / warning / error / critical)',
                        type=str, default=LOG_LEVEL)
    PARSER.add_argument('-j', '--json',
                        help='File with list of actions to execute)',
                        type=str, default=JSON_CONFIG)
    OPTIONS = PARSER.parse_args()

    # Logging configuration
    LEVELS = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}
    LOGLEVEL = LEVELS.get(OPTIONS.debug_level, logging.NOTSET)
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=LOGLEVEL,
        datefmt='%Y-%m-%d %H:%M:%S')

    # activate SSL enforcement or not
    # (should be disabled for self-signed certs)
    if cvprac_abstraction.CERT_VALIDATION is False:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    logging.debug('CVP Client inputs:')
    logging.debug('  > Username is %s', OPTIONS.username)
    logging.debug('  > Server is %s', OPTIONS.cvp)
    logging.debug('  > Port is %s', CVP['PORT'])
    logging.debug('  > Proto is %s', CVP['PROTO'])
    print '\n--------------------\n'

    # Parse actions defined in OPTIONS.json
    # Based on action field, script will execute different
    # set of actions
    LIST_ACTIONS = config_read(config_file=OPTIONS.json)
    for ACTION in LIST_ACTIONS:
        if 'type' not in ACTION:
            logging.critical('task %s does not have type defined - skipping', ACTION['name'])  # noqa E501
            break
        if 'action' in ACTION and ACTION['type'] == 'configlet':
            if ACTION['action'] == 'add':
                logging.info('configlet %s is going to be created %s',
                             ACTION['name'],
                             ACTION['configlet'])
                action_add(configlet_def=ACTION, parameters=OPTIONS)
            elif ACTION['action'] == 'delete':
                logging.info('configlet %s is going to be deleted %s',
                             ACTION['name'],
                             ACTION['configlet'])
                action_delete(configlet_def=ACTION, parameters=OPTIONS)
            elif ACTION['action'] == 'update':
                logging.info('configlet %s is going to be updated %s',
                             ACTION['name'],
                             ACTION['configlet'])
                action_update(configlet_def=ACTION, parameters=OPTIONS)
            elif ACTION['action'] == 'remove-devices':
                logging.info('configlet %s is going to be removed from devices',
                             ACTION['name'])
                action_remove_devices(configlet_def=ACTION, parameters=OPTIONS)
            elif ACTION['action'] == 'add-devices':
                logging.info('configlet %s is going to be added to devices',
                             ACTION['name'])
                action_add_devices(configlet_def=ACTION, parameters=OPTIONS)
            else:
                logging.error('Unsupported action.\
                                Please use add / delete / update only')
            print '\n--------------------\n'
        elif ACTION['type'] == 'change-control':
            logging.info('Implementation in progress -- expect some issues')
            action_create_change_control(OPTIONS, ACTION)
        else:
            logging.warning('task is not supported -- skipping')
        logging.info('Wait 10 sec before next action')
        time.sleep(10)
