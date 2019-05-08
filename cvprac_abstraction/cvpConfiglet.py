import sys
import os
import logging
import time
from cvpInventory import CvpInventory
from cvprac_abstraction import CVP
from cvprac.cvp_client_errors import CvpLoginError
from cvprac.cvp_client_errors import CvpApiError


class CvpConfiglet(object):
    """Configlet class to provide generic method to manage CVP configlet.

    **Data Structure**

    Configlet structure is a name based dictionnary with following keys:

    - ``name``: Name of configlet. This name is built from filename
    - ``file``: Complete path of the local configlet file
    - ``content``: Local Configlet content read from ``configlet['file']``
    - ``key``: Key ID defined by CVP to identify configlet.
        it is found by our instance during update, addition or deletion
    - ``devices``: List of devices structure compliant
        with ``CvpApi.get_device_by_name()`` It can be found by
        using ``CvpInventory`` object.

    **List of attributes:**

    Attributes
    ----------
    _cvp_server
        cvprac.CvpClient() object to manage CVP connection
    _devices_configlet
        List of devices attached to configlet
    _configlet
        Dictionary with all configlet information: ``name``, ``file``,
        ``content``, ``key``, ``devices``
    _cvp_found
        Boolean to get status of configlet on CVP: True if configlet is on
        server, False other cases


    **List of public available methods:**

    Methods
    -------
    get_devices()
        Get list of devices for this specific configlet
    update_configlet()
        Start update process for that configlet.
        Do not deploy content to devices
    deploy_configlet()
        Start configlet creation process.
        Do not deploy content to devices
    delete_configlet()
        Start configlet deletion process. Do not deploy content to devices
    deploy()
        Deploy (add/update) change to a single device
    deploy_bulk()
        Deploy (add/update) change to all devices
    on_cvp()
        Inform about configlet available on CVP

    Example
    -------

        >>> from cvprac_abstraction import CVP
        >>> from cvprac_abstraction import connect_to_cvp
        >>> from cvprac_abstraction.cvpConfiglet import CvpConfiglet
        >>> 
        >>> parameters['cvp'] = '127.0.0.1'
        >>> parameters['username'] = 'arista'
        >>> parameters['password'] = 'arista'
        >>> 
        >>> client = connect_to_cvp(parameters)
        >>> 
        >>> my_configlet = CvpConfiglet(cvp_server=client,configlet_file='/path/to/configlet')
        >>> 
        >>> my_configlet.update_configlet()
        >>> 
        >>> my_configlet.deploy_bulk()

    Note
    ----

    This class use calls to ``cvprac`` to get and push data to CVP server.

    """

    def __init__(self, cvp_server, configlet_file=None, configlet_name=None):
        r"""Class Constructor.

        Parameters
        ----------
        ``cvp_server``: CvpClient
            CvpClient object from cvprack. Gives methods to manage CVP API
        ``configlet_file``: str
            Path to configlet file.

        """
        self._cvp_server = cvp_server
        # create data storage for configlet
        # and tasks related to deployment
        self._configlet_init()
        self._task_init()
        self._devices_configlet = list()
        # Extract information from configlet filename
        if configlet_file is not None:
            self._configlet['file'] = configlet_file
            self._configlet['name'] = os.path.basename(configlet_file)
            logging.debug('configlet basename is [%s]',
                          self._configlet['name'])
        if configlet_name is not None:
            self._configlet['name'] = configlet_name

        # check if configlet is present on CVP server
        if self._configlet_lookup():
            logging.info('Configlet [%s] found on %s', self._configlet['name'],
                         CVP['HOST'])
            logging.info('Get list of applied devices from server')
            self.get_devices(refresh=True)
            self._cvp_found = True
        else:
            self._cvp_found = False
            logging.warning('Configlet NOT found on %s', CVP['HOST'])

    def _configlet_lookup(self):
        """Check if a configlet is already present on CVP.

        Check if CVP has already a configlet configured with the same name.
        If yes return True and report key under self._configlet['key']
        If no, return False

        Returns
        -------
        bool
            Return ``True`` or ``False`` if configlet name is
            already configured on CVP

        """
        try:
            result = self._cvp_server.api.get_configlet_by_name(name=self._configlet['name'])  # noqa E501
            if 'key' in self._configlet:
                self._configlet['key'] = result['key']
            return True
        except CvpApiError:  # noqa E722
            return False

    def _configlet_init(self):
        """Create an empty dict for configlet."""
        logging.debug('Init configlet object')
        self._configlet = dict()
        self._configlet['name'] = None
        self._configlet['file'] = None
        self._configlet['content'] = None
        self._configlet['key'] = None
        self._configlet['devices'] = list()

    def _task_init(self):
        """Create an empty dict for task."""
        logging.debug('Init task object')
        self._task = dict()
        self._task['id'] = None
        self._task['run_at'] = None
        self._task['result'] = None

    def name(self):
        """Expose name of the configlet.

        Returns
        -------
        str
            Name of configlet built by ``__init__``

        """
        return self._configlet['name']

    def on_cvp(self):
        """Expose flag about configlet configured on CVP.

        Return True if configlet is configured on CVP and can be updated.
        If configlet is not present, then, False

        Returns
        -------
        bool
            True if configlet already configured on CVP, False otherwise

        """
        return self._cvp_found

    def _retireve_devices(self):
        r"""Get list of devices attached to the configlet.

        If configlet exists, then, retrieve a complete list of devices
        attached to it.

        Returns
        -------
        list
            List of devices from CVP

        """
        self._devices_configlet = list()
        inventory = CvpInventory(self._cvp_server).get_devices()
        logging.info('Start looking for devices attached to [%s]',
                     self._configlet['name'])
        for device in inventory:
            if 'systemMacAddress' in device:
                try:
                    configlet_list = self._cvp_server.api.get_configlets_by_device_id(mac=device['systemMacAddress'])  # noqa E501
                except CvpLoginError, e:
                    logging.error('Error when getting list of configlet for device %s: %s', device['hostname'], str(e).replace('\n', ' '))  # noqa E501
                    quit()
                for configlet in configlet_list:
                    logging.debug('  > Found configlet: %s for device [%s]', configlet['name'], device['hostname'])  # noqa E501
                    if configlet['name'] == self._configlet['name']:
                        self._configlet['devices'].append(device)
                        logging.info('  > Configlet [%s] is applied to %s with sysMacAddr %s', self._configlet['name'], device['hostname'], device['systemMacAddress'])  # noqa E501
        return self._devices_configlet

    def get_configlet_info(self):
        """To share configlet information.

        Returns
        -------
        dict
            dictionnary with configlet information

        """
        return self._configlet

    def get_devices(self, refresh=False):
        r"""To share list of devices attached to the configlet.

        If list is empty or if refresh trigger is active,
        function will get a new list of device from self._retireve_devices()
        Otherwise, just send back list to the caller

        Parameters
        ----------
        refresh : bool
            Update device list from CVP (Optional)

        Returns
        -------
        list
            List of devices from CVP

        """
        if refresh or 'devices' not in self._configlet:
            self._retireve_devices()
        return self._configlet['devices']

    def update_configlet(self):
        """Update configlet on CVP with content from object.

        Check if configlet is configured on CVP server before pushing an update.
        If configlet is not there, then, stop method execution.

        Returns
        -------
            str : message from server with result

        """
        logging.info('%s is going to be updated with local config',
                     self._configlet['name'])
        try:
            with open(self._configlet['file'], 'r') as content:
                configlet = content.read()
            status_deployment = self._cvp_server.api.update_configlet(key=self._configlet['key'],  # noqa E501
                                                                      name=self._configlet['name'],  # noqa E501
                                                                      config=configlet)  # noqa E501
            logging.warning('Server response: %s', status_deployment['data'])
            return status_deployment['data']
        except IOError:
            logging.critical('!! File not found: %s',
                             self._configlet['file'])
            sys.exit()

    def deploy_configlet(self, device_hostnames):
        """Create configlet on CVP with content from object.

        Create a new configlet on CVP server and attached it to all devices
        you provide in your JSON file.
        Device attachement is managed with a CvpInventory call
        to get all information from CVP.
        It means you just have to provide existing hostname in your JSON

        Each time a device is attached to configlet on CVP, it is also added
        in CvpConfiglet object for futur use

        Parameters
        ----------
        devices_hostname : list
            List of hostname to attached to configlet

        """
        logging.info('Create configlet %s', self._configlet['name'])
        with open(self._configlet['file'], 'r') as content:
            self._configlet['content'] = content.read()
        self._configlet['key'] = self._cvp_server.api.add_configlet(name=self._configlet['name'],  # noqa E501
                                                                    config=self._configlet['content'])  # noqa E501
        # Use method to attach device to configlet.
        self.add_device(device_hostnames=device_hostnames)

    def delete_configlet(self):
        """Delete a configlet from CVP.

        To protect, function first check if configlet exists, if not, we stop
        and return to next action out of this function.
        Remove configlet from all devices where it is configured
        Then if configlet exist, remove configlet from CVP DB

        Returns
        -------
        bool
            ``True`` if able to remove configlet / False otherwise

        """
        logging.info('start to remove %s from CVP', self._configlet['name'])
        if self._configlet['key'] is None:
            logging.critical('Configlet not configured. Can\'t remove it')
            return False
        impacted_devices = self.get_devices()
        for device in impacted_devices:
            logging.info('[%s] - remove configlet %s', device['hostname'],
                         self._configlet['name'])
            self._cvp_server.api.remove_configlets_from_device(app_name='CVP Configlet Python Manager', dev=device, del_configlets=[self._configlet])  # noqa E501
        logging.info('remove %s from CVP', self._configlet['name'])
        self._cvp_server.api.delete_configlet(name=self._configlet['name'],
                                              key=self._configlet['key'])
        return True

    def add_device(self, device_hostnames):
        """Remove device(s) from a configlet.

        Remove device from configlet and create a task on CVP to remove
        configuration generated by configlet from device.
        For every hostname defined in devices_hostnames, a lookup is done to get
        a complete data set for that device and a call to remove device is sent.

        Warnings
        --------
        This function never send a call to execute task. it is managed by logic
        out of that object

        Arguments:
            devices_hostnames {list} -- List of devices hostname to remove from
                the configlet.
        """
        cvp_inventory = CvpInventory(cvp_server=self._cvp_server)
        logging.info('add devices to configlet %s',
                     self._configlet['name'])

        for host in device_hostnames:
            eos = cvp_inventory.get_device_dict(name=host)
            if eos is not None:
                logging.info('Apply configlet %s to %s',
                             self._configlet['name'],
                             eos['hostname'])
                self._configlet['devices'].append(eos)
                self._cvp_server.api.apply_configlets_to_device(app_name='Apply configlet to device', dev=eos, new_configlets=[self._configlet])  # noqa E501
        logging.info('Configlet %s has been applied to all devices',
                     self._configlet['name'])

    def remove_device(self, devices_hostnames):
        """Remove device(s) from a configlet.

        Remove device from configlet and create a task on CVP to remove
        configuration generated by configlet from device.
        For every hostname defined in devices_hostnames, a lookup is done to get
        a complete data set for that device and a call to remove device is sent.

        Warnings
        --------
        This function never send a call to execute task. it is managed by logic
        out of that object

        Arguments:
            devices_hostnames {list} -- List of devices hostname to remove from
                the configlet.
        """
        cvp_inventory = CvpInventory(cvp_server=self._cvp_server)

        logging.info('remove devices from configlet %s',
                     self._configlet['name'])

        for host in devices_hostnames:
            eos = cvp_inventory.get_device_dict(name=host)
            if eos is not None:
                logging.info('remove configlet %s from %s',
                             self._configlet['name'],
                             eos['hostname'])
                self._cvp_server.api.remove_configlets_from_device(app_name='Python Configlet Remove device', dev=eos, del_configlets=[self._configlet])  # noqa E501
        logging.info('Configlet %s has been updated by removing some devices',
                     self._configlet['name'])

    @classmethod
    def _get_task_id(cls, task_reply):
        """Extract task ID from server reply.

        When running api.apply_configlets_to_device() CVP server
        sends back a complete message. This function extract specific
        taskId field to then track it in the task manager

        Parameters
        ----------
        task_reply : dict
            Server reply to a api.apply_configlets_to_device

        Returns
        -------
        str
            taskID sent by server

        """
        if 'data' in task_reply:
            if 'taskIds' in task_reply['data']:
                logging.debug('Task ID is %s', task_reply['data']['taskIds'])
                return task_reply['data']['taskIds'][0]
        return None

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

    def deploy(self, device, schedule_at=None, task_timeout=10):
        r"""Deploy One configlet to One device.

        This function manage a deployment this configlet to a
        given device already attached to the configlet.

        Parameters
        ----------
        device : dict
            dict representing a device
        schedule_at : str
            Optional - scheduler to run deployment at a given time
        task_timeout : int
            Optional - Timeout for task execution default is 10 seconds

        Warnings
        --------
        ``schedule_at`` option is not yet implemented and shall not be used

        Returns
        -------
        dict
            message from server

        """
        if schedule_at is None:
            logging.warning('[%s] - Configlet %s is going to be deployed \
                immediately', device['hostname'], self._configlet['name'])
            configlet_deploy = self._cvp_server.api.apply_configlets_to_device(
                app_name='Update devices',
                dev=device,
                new_configlets=[self._configlet],
                create_task=True)
            # Create task on CVP to update a device
            task_id = self._get_task_id(task_reply=configlet_deploy)
            task_status = self._cvp_server.api.get_task_by_id(int(task_id))
            logging.info('[%s] - Task %s status : %s',
                         device['hostname'],
                         str(task_id),
                         str(task_status['taskStatus']).upper())
            # Execute task
            self._cvp_server.api.execute_task(task_id=task_id)
            task_status = self._wait_task(task_id=task_id,
                                          timeout=task_timeout)
            logging.info('[%s] - Task %s status : %s',
                         device['hostname'],
                         str(task_id),
                         str(task_status['taskStatus']).upper())
            task = dict()
            task['id'] = task_id
            task['status'] = task_status
            return task
        return None

    def deploy_bulk(self,
                    device_list=None,
                    schedule_at=None,
                    task_timeout=10):
        """Run configlet deployment against all devices.

        Run configlet deployment over all devices attached to this configlet.
        Every single deployment are managed by function self.deploy()

        Parameters
        ----------
        device_list : list
            List of devices if it is set to None, then,
            fallback is to use devices discover initially
        at : str
            Optional scheduler to run deployment at a given time
        task_timeout : int
            Optional - Timeout for task execution. Default is 10 seconds

        Warnings
        --------
        ``schedule_at`` option is not yet implemented and shall not be used

        Returns
        -------
        list
            A list of tasks executed for the deployment

        """
        tasks = list()
        logging.warning('Start tasks to deploy configlet %s to devices',
                        self._configlet['name'])
        if device_list is None:
            device_list = self._configlet['devices']
        for dev in device_list:
            if 'systemMacAddress' not in dev or 'hostname' not in dev:
                # If information are missing, then we can't deploy using API
                logging.warning('[%s] - information are missing to run \
                                deployment of %s',
                                dev['hostname'],
                                self._configlet['name'])
                break
            # Assuming we have enought information to deploy
            logging.info('[%s] - Start to update device with configlet %s',
                         dev['hostname'],
                         self._configlet['name'])
            task = self.deploy(device=dev, schedule_at=None,
                               task_timeout=task_timeout)
            # Parsing task content to see if we can append to the list or not.
            if 'taskStatus' in task['status']:
                if task['status']['taskStatus'].upper() == 'COMPLETED':
                    logging.info('[%s] - Updated',
                                 dev['hostname'])
                    tasks.append(task)
                else:
                    logging.error('[%s] - Not updated as expected, \
                                  please check your CVP',
                                  dev['hostname'])
                    logging.error('[%s] - Status is: %s',
                                  dev['hostname'],
                                  task['status'])
        return tasks
