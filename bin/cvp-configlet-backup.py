#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import os
import argparse
import logging
import pprint
import json
import cvprac_abstraction
from cvprac_abstraction import CVP, LOG_LEVEL
from cvprac_abstraction import connect_to_cvp
import requests
# Import to optionnaly disable HTTPS cert validation
from requests.packages.urllib3.exceptions import InsecureRequestWarning

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
    PARSER.add_argument('-b', '--backup',
                        help='Backup folder to save configlets. Default is ${CVP_BACKUP}',
                        type=str, default=CVP['CONFIGLET_BACKUP'])
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

    # Check and create backup folder
    logging.info('* check if backup folder exists.')
    path = os.getcwd()
    if os.path.isdir(CVP['CONFIGLET_BACKUP']) is False:
        logging.warning(' -> local folder does not exist. create it !')
        os.mkdir(CVP['CONFIGLET_BACKUP'])
    os.chdir(CVP['CONFIGLET_BACKUP'])

    logging.info('* connecting to cloudvision server %s', CVP['HOST'])
    cvp_server = connect_to_cvp(parameters=OPTIONS)

    logging.info('* extracting configlet from cloudvision server')
    configlets_list = cvp_server.api.get_configlets()
    pp = pprint.PrettyPrinter(indent=2)
    for configlet in configlets_list['data']:
        logging.info(' -> exporting configlet %s', configlet['name'])
        # Get a file object with write permission.
        file_object = open("configlet-" + configlet['name'].replace(' ', '-') + ".json", 'w')
        # Save dict data into the JSON file.
        json.dump(configlet, file_object, indent=4, sort_keys=True)
    logging.info('* backup complete. Configlets have been saved in %s', CVP['CONFIGLET_BACKUP'])
