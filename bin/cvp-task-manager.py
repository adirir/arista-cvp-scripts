#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import argparse
import logging
import time
import cvprac_abstraction
from cvprac_abstraction import CVP, LOG_LEVEL
from cvprac_abstraction import connect_to_cvp
import requests
# Import to optionnaly disable HTTPS cert validation
from requests.packages.urllib3.exceptions import InsecureRequestWarning

"""Script to interact with task on Arista CloudVision server.

This script provides a CLI method to play with Arista CloudVision server and
execute pending tasks.

It is based on cvprac library.

Supported CVP Version:
----------------------
- 2018.1.2
- 2018.2.x

Supported Features:
-------------------

- List all pending tasks on a CVP server

    $ python bin/cvp-task-manager.py -l

- Execute all pending tasks on a CVP server

    $ python bin/cvp-task-manager.py -ra -t 120

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

"""


class CvpTaskManager(object):
    """CVP Task manager.

    Python Class to interact with tasks management on Arista CloudVision.
    Provides abstraction to list and execute pending tasks on a CVP server
    """
    def __init__(self, cvp_server):
        """Class Constructor.

        Build class content with followinactivities:
            - save cvp_server information
            - instanciate list for pending tasks
            - Collect tasks available from CVP

        Parameters
        ----------
        cvp_server : CvpClient
            CVP Server information

        """
        logging.debug('create instance of CvpChangeControl')
        self._cvp_server = cvp_server
        # List of available tasks from server
        self._available = list()
        # List to save tasks to run with their order
        # Ex: [{'taskId': '100', 'taskOrder': 1},
        #     {'taskId': '101', 'taskOrder': 1},
        #     {'taskId': '102', 'taskOrder': 2}]
        self._list_changes = list()
        self._retrieve_tasks()

    def _wait_task(self, task_id, timeout=10):
        """Wait for Task execution.

        As API call is asynchronous, task will run avec after
        receiving a status.
        This function implement a wait_for to get final status of a task
        As we have to protect against application timeout or task issue,
        a basic timeout has been implemented

        Parameters
        ----------
        task_id : str
            ID of the task provided by self._get_task_id()
        timeout : int
            optional - Timeout to wait for before assuming task failed

        Returns:
        --------
        dict
            Last status message collected from the server

        """
        state = dict()
        state['taskStatus'] = None
        loop_timer = 0
        while str(state['taskStatus']) != 'COMPLETED' and loop_timer < timeout:
            time.sleep(1)
            state = self._cvp_server.api.get_task_by_id(int(task_id))
            logging.debug('  ** Wait for task completion (status: %s) / waiting for %s sec',  # noqa E501
                          state['taskStatus'],
                          str(loop_timer))
            loop_timer += 1
        return state

    def _retrieve_tasks(self):
        """Extract tasks from CVP Server.

        Connect to CVP server and collect tasks in pending state
        These tasks are saved in self._available structure dedicated
        to pending tasks.

        """
        logging.debug('getting list of available task for change control')
        self._available = self._cvp_server.api.change_control_available_tasks()

    def get_tasks(self, refresh=False):
        """Provide list of all available tasks.

        Return list of all tasks getting from CVP and/or attached
        with add_task method.

        Parameters
        ----------
        refresh : bool
            Optional - Make a call to CVP to get latest list of tasks

        Returns
        -------
            list
                List of available tasks found in this CC

        """
        logging.debug('extractig list of pending tasks')
        if refresh:
            logging.debug('refreshing list of tasks in pending state')  # noqa E501
            self._retrieve_tasks()
        return self._available

    def deploy(self, task_id, task_timeout=10):
        r"""Send API call to execute a pending task

        Parameters
        ----------
        task_id : int
            Task ID to execute on CVP server.
        task_timeout : int, optional
            Timer to wait to collect task status, by default 10

        Returns
        -------
        dict
            A dict with task ID and status sent back by CVP.
        """
        # Execute task
        self._cvp_server.api.execute_task(task_id=task_id)
        task_status = self._wait_task(task_id=task_id,
                                      timeout=task_timeout)
        logging.info('Task %s status : %s',
                     str(task_id),
                     str(task_status['taskStatus']).upper())
        task = dict()
        task['id'] = task_id
        task['status'] = task_status
        return task

    def deploy_all(self, task_timeout=10):
        """Manage execution of all pending tasks collected on CVP.

        Parameters
        ----------
        task_timeout : int, optional
            Timer to wait to collect task status, by default 10
        """
        for task in self._available:
            logging.info('Found task %s - startig execution',
                         str(task['workOrderId']))
            task_result = self.deploy(task_id=task['workOrderId'],
                                      task_timeout=task_timeout)
            logging.info(' > Task %s has been returned with status %s',
                         str(task['workOrderId']), str(task_result['status']['taskStatus']))


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
    PARSER.add_argument('-t', '--task_timeout',
                        help='Timeout to wait for task execution',
                        type=int, default=10)
    PARSER.add_argument('-ra', '--run_all',
                        help='Execute all pending tasks on CVP',
                        action='store_true')
    PARSER.add_argument('-l', '--list',
                        help='List all pending tasks on CVP',
                        action='store_true')
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

    logging.info('connecting to cvp server')
    cvp_client = connect_to_cvp(OPTIONS)
    taskManager = CvpTaskManager(cvp_server=cvp_client)

    if OPTIONS.run_all is True:
        logging.info('* script will execute all pending tasks')
        taskManager.deploy_all(task_timeout=OPTIONS.task_timeout)
    elif OPTIONS.list is True:
        logging.info('* listing all pending tasks')
        for task in taskManager.get_tasks():
            logging.info('  > Task %s - %s',
                         str(task['workOrderId']), str(task['description']))
    print '\n--------------------\n'
