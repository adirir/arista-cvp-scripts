#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import argparse
import logging
import time
import cvprac_abstraction
from cvprac_abstraction import CVP, LOG_LEVEL, JSON_CONFIG
from cvprac_abstraction import connect_to_cvp, config_read
from cvprac_abstraction.cvpContainer import CvpContainer
import requests
# Import to optionnaly disable HTTPS cert validation
from requests.packages.urllib3.exceptions import InsecureRequestWarning

r"""Script to manage manage container on CloudVision Portal.

This script allows user to manage containers defined on CloudVision platform.
Current version supports only option to move a device from one container to another one.
It uses a JSON file as an input to list all actions to run. This JSON file shall use following syntax:

JSON Example
------------

Input example::

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
        }
    ]

CLI Examples
------------

- Generic method using JSON inputs::

    $ python arista-cvp-container-manager -j actions.json

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

"""


def action_container_create(tasker, parameters):
    """Worker to create a container.

    Implement script logic to create a container on CVP.

    Parameters
    ----------
    tasker : dict
        Information from JSON file describing action to run.
    parameters : dict
        CVP Connection information.
    """
    # Create an HTTP session to the CVP server
    logging.debug('connect to CVP server')
    client = connect_to_cvp(parameters)

    logging.info('*************')
    logging.info('Start working with %s', tasker['container'])

    container = CvpContainer(name=tasker['container'], cvp_server=client)

    logging.info('create container on CVP server')
    container.create(parent_name=tasker['parent'])


def action_container_destroy(tasker, parameters):
    """Worker to destroy a container.

    Implement script logic to remove a container from CVP topology.

    Parameters
    ----------
    tasker : dict
        Information from JSON file describing action to run.
    parameters : dict
        CVP Connection information.
    """
    # Create an HTTP session to the CVP server
    logging.debug('connect to CVP server')
    client = connect_to_cvp(parameters)

    logging.info('*************')
    logging.info('Start working with %s', tasker['container'])

    container = CvpContainer(name=tasker['container'], cvp_server=client)

    logging.info('destroy container from CVP server')
    container.destroy(parent_name=tasker['parent'])


def action_attach_device(tasker, parameters):
    """Worker to attach device to configlet.

    Implement script logic to move a device from one container to another one.

    Parameters
    ----------
    tasker : dict
        Information from JSON file describing action to run.
    parameters : dict
        CVP Connection information.
    """
    # Create an HTTP session to the CVP server
    logging.debug('connect to CVP server')
    client = connect_to_cvp(parameters)

    logging.info('*************')
    logging.info('Start working with %s', tasker['container'])

    container = CvpContainer(name=tasker['container'], cvp_server=client)

    # logging.info('getting info for container %s', tasker['container'])
    # info = container.get_info()

    logging.info('check is devices are already part of container')
    for device in tasker['devices']:
        if container.is_device_attached(hostname=device):
            logging.critical('device is already part of that container -- skipping')
        else:
            logging.info('device is not part of that container -- moving forward')
    container.attach_device_bulk(hostname_list=tasker['devices'], deploy=tasker['apply'])


if __name__ == '__main__':
    # Argaparser to load information using CLI
    PARSER = argparse.ArgumentParser(description="Cloudvision Container Manager",
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
        if 'action' in ACTION and ACTION['type'] == 'container':
            if ACTION['action'] == 'attach-device':
                for hostname in ACTION['devices']:
                    logging.info('device %s is going to be moved to %s',
                                 hostname,
                                 ACTION['container'])
                action_attach_device(tasker=ACTION, parameters=OPTIONS)
            elif ACTION['action'] == 'create':
                logging.info('creation of container with name %s attached to %s',
                             ACTION['container'],
                             ACTION['parent'])
                action_container_create(tasker=ACTION, parameters=OPTIONS)
            elif ACTION['action'] == 'destroy':
                logging.info('destruction of container with name %s',
                             ACTION['container'])
                action_container_destroy(tasker=ACTION, parameters=OPTIONS)
            else:
                logging.error('Unsupported action. Please report to documentation')
            print '\n--------------------\n'
        else:
            logging.warning('task is not supported -- skipping')
        logging.info('Wait 10 sec before next action')
        time.sleep(10)
