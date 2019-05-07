import logging
import time
from cvpInventory import CvpInventory


class CvpContainer(object):
    """Class to manage Container on CVP.

    Centralize a abstraction layer of CVPRAC to manage actions related to container.

    **List of public available methods:**

    Methods
    -------
    create()
        Create a new container on CloudVision Platform
    destroy()
        Delete an existing with no attached devices container on CloudVision Platform
    is_device_attached()
        Poll CVP to know if a device is already part of given container
    get_info()
        Get container's information from CVP server
    attach_device()
        Create a task to attach a given device to container
    attach_device_bulk()
        Create a list of tasks to attach many devices to container
    run_pending()
        Execute all pengind tasks created by cvpContainer object.

    Note::
    ------

    This class use calls to ``cvprac`` to get and push data to CVP server.

    

    """
    def __init__(self, name, cvp_server):
        """Class Constructor.

        Parameters
        ----------
        name : str
            container's name to look for on CloudVision server
        cvp_server : cvprack.CvpClient()
            Object in charge of sending API calls to CVP server.

        Returns
        -------
        None
        """
        logging.info('initializing a container object for %s', name)
        # Container name provided by user
        self._name = name
        # CvpServer connection manager
        self._cvp_server = cvp_server
        # CvpInventory to collect devices information
        self._inventory = CvpInventory(self._cvp_server)
        # Container info collecting from CVP server
        self._info = self._container_info()
        # List to save pending tasks related to container changes
        self._tasks = list()
        # Provisionned a structure to save attached devices
        self._attached_devices_dict = None
        # Check if container exists already.
        # If not, inform user
        # else, get JSON information for latter use.
        if self._info is None:
            logging.warning('container %s not found', name)
        else:
            self._get_devices()

    def create(self, parent_name='Tenant'):
        """Create a container on CVP.

        Implement workflow to create a container on CVP. Manage following actions:
        - Collect Parent container information
        - Create container.

        Parameters
        ----------
        parent_name : str, optional
            Name of parent container to use to attach container, by default 'Tenant'
        """
        logging.info('start creation of container attached to %s', parent_name)
        parent_container = self._container_info(name=parent_name)
        if parent_name is not None and self._info is None:
            self._cvp_server.api.add_container(container_name=self._name, parent_name=parent_container['name'], parent_key=parent_container['key'])
        elif self._info is not None:
            logging.error('cannot create container %s -- already configured on CVP', self._name)
        elif parent_name is None:
            logging.error('cannot create container %s -- parent container is required', self._name)
        else:
            logging.error('cannot create container %s', self._name)

    def destroy(self, parent_name="Tenant"):
        """Remove a container from CVP topology.

        Parameters
        ----------
        parent_name : str, optional
            Name of the parent container, by default "Tenant"

        Returns
        -------
        None

        """
        logging.info('start process to delete container %s', self._name)
        parent_container = self._container_info(name=parent_name)
        if len(self._attached_devices_dict) > 0:
            logging.error('cannot remove container %s.', self._name)
            logging.error('  Reason: container is not empty (%s devices remain)',
                          str(len(self._attached_devices_dict)))
            return None
        self._cvp_server.api.delete_container(container_name=self._name,
                                              container_key=self._container_id(),
                                              parent_name=parent_container['name'],
                                              parent_key=parent_container['key'])

    def _container_info(self, name=None):
        """Pull CVP to get container information.

        Execute a call against CVP to get a dict of information.

        Structure is::

            {
                u'dateTimeInLongFormat': 1513002053415,
                u'key': u'container_8_2864853689536',
                u'mode': u'expand',
                u'name': u'CVX',
                u'root': False,
                u'undefined': False,
                u'userId': u'arista'
            }

        Parameters
        ----------
        name : [type], optional
            Name of container to pull. If not set, name of container used for this instance is configured, by default None

        Returns
        -------
        dict
            Structure sent back by CVP
        """
        if name is None:
            name = self._name
        result = None
        result = self._cvp_server.api.get_container_by_name(name)
        if result is not None:
            return result
        return None

    def _container_id(self, name=None):
        """Get Container ID based on its name.

        Parameters
        ----------
        name : str, optional
            Container name to get ID, by default None

        Returns
        -------
        str
            container ID configured on CVP
        """
        if name is None:
            name = self._name
        result = None
        result = self._container_info(name)
        if result is not None:
            return result['key']
        return None

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
            logging.info('  * Wait for task completion (status: %s) / waiting for %s sec',  # noqa E501
                          state['taskStatus'],
                          str(loop_timer))
            loop_timer += 1
        return state

    def _get_devices(self):
        """Get list of devices attached to container.

        Extract information from CVP to get complete list of devices attached to this container on CVP.
        Result is saved part of this object.

        """
        logging.debug('collecting list of attached devices')
        self._attached_devices_dict = self._cvp_server.api.get_devices_in_container(name=self._name)

    def is_device_attached(self, hostname):
        """Test wether or not a device is part of container.

        Test if device hostname is already attached to this container. it is based on list provided by self._get_devices()

        Parameters
        ----------
        hostname : str
            Hostname to search in container.

        Returns
        -------
        boolean
            True if device is part of container, False if not found.
        """
        logging.debug('search if device is already attached to container %s', self._name)
        # No device attached to container, then return false.
        if self._attached_devices_dict is None:
            return False
        # Container has some devices, the searching for hostname.
        for device in self._attached_devices_dict:
            if hostname == device['hostname']:
                return True
        return False

    def attach_device(self, hostname, deploy=False):
        """Move device to container

        Move device within container represented in this object.
        This method create a task to be executed later by user or by the script itself.

        Parameters
        ----------
        hostname : str
            Hostname to move to this container. Complete data set is pulling from
                CVP if device exists and not attached to this container already.
        deploy : bool, optional
            Boolean to manage deployment. Not used in this function, by default False

        Returns
        -------
        str
            Task ID created by the change on CVP.
        """

        logging.info('>---')
        device_info = self._inventory.get_device_dict(name=hostname)
        if device_info is not None:
            if self.is_device_attached(hostname=hostname) is False:
                logging.info('create change to move %s to %s', hostname, self._name)
                task_reply = self._cvp_server.api.move_device_to_container(app_name='device move', device=device_info, container=self._info)
                # Return per action: { u'data': { u'status': u'success', u'taskIds': [u'222']}}
                task_id = self._get_task_id(task_reply=task_reply)
                if task_id is not None:
                    logging.info('task created on CVP: %s', task_id)
                    return task_id
                else:
                    return None
            else:
                logging.critical('device already attached to %s', self._name)
        else:
            logging.error('device %s not found on CVP', hostname)
            return None

    def run_pending(self, task_timeout=10):
        """Execute pending tasks related to container

        Run tasks created when you change container.
        It does not manage tasks from other objects.

        Parameters
        ----------
        task_timeout : int, optional
            timer to wait for task completion, by default 10

        Returns
        -------
        list()
            A list of dictionary where every entry is result of a task::
                [{id:200, status: completed}, {id:201, status: completed}]
        """
        logging.info('>---')
        logging.info('run pending tasks to related to container %s', self._name)
        task_list = list()
        for task in self._tasks:
            logging.info(' -> execute task ID: %s', str(task))
            # Execute task
            self._cvp_server.api.execute_task(task_id=task)
            task_status = self._wait_task(task_id=task,
                                          timeout=task_timeout)
            logging.info(' -> task %s status : %s',
                         str(task),
                         str(task_status['taskStatus']).upper())
            task_result = dict()
            task_result['id'] = task
            task_result['status'] = task_status
            task_list.append(task_result)
        # Remove all pending tasks
        self._tasks = None
        return task_list

    def attach_device_bulk(self, hostname_list, deploy=False):
        """Attach a list of device to existing container.

        Get a list of hostname to move to current container. For every hostname,
        a call to CVP is sent to get device's information and build structure to
        move it to appropriate container.

        Parameters
        ----------
        hostname_list : list
            List of device hostname to attach to container.
        deploy : bool, optional
            Trigger to execute tasks generated during the attach phase, by default False
        """
        logging.info('>---')
        logging.info('starting process to attach a list of device to %s', self._name)
        for hostname in hostname_list:
            result = self.attach_device(hostname=hostname)
            if result is not None:
                self._tasks.append(result)
        if deploy:
            self.run_pending()

    def get_info(self):
        """Return container's information.

        Return container's information pulling from CloudVision server.

        Structure is::

            {
                u'dateTimeInLongFormat': 1513002053415,
                u'key': u'container_8_2864853689536',
                u'mode': u'expand',
                u'name': u'CVX',
                u'root': False,
                u'undefined': False,
                u'userId': u'arista'
            }

        Returns
        -------
        dict
            Container information from CVP
        """
        logging.debug('extracting info for container %s', self._name)
        return self._info
