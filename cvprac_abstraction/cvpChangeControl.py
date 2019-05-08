import logging
from datetime import datetime
from datetime import timedelta
from cvprac.cvp_client_errors import CvpApiError


class CvpChangeControl(object):
    """Change-control class to provide generic method for CVP CC mechanism.

    Change Control structure is based on:
        - A name to identify change
        - A list of tasks already created on CVP and on pending state
        - An optional scheduling. If no schedule is defined,
            then task will be run 3 minutes after creatio of CC

    **List of public available methods:**

    Methods
    -------
    add_task()
        Append a task to self._list_changes
    get_tasks()
        Return list of of available tasks for this CC
    get_list_changes()
        Return list of tasks attached to this CC
    create()
        Create change-control on CVP server

    Example
    -------

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

    Warnings
    --------

    - Change Control execution is not running snapshot before and after with cvprac 1.0.1

    """

    def __init__(self, cvp_server, name='Automated_Change_Control'):
        """Class Constructor.

        Build class content with followinactivities:
            - save cvp_server information
            - save name for CC
            - instanciate list for tasks
            - Collect tasks available from CVP

        Parameters
        ----------
        cvp_server : CvpClient
            CVP Server information
        name : str
            Optional - Name of the Change Control.
            Default is ``Automated_Change_Control``

        """
        logging.debug('create instance of CvpChangeControl')
        self._cvp_server = cvp_server
        self._name = name
        # List of available tasks from server
        self._available = list()
        # List to save tasks to run with their order
        # Ex: [{'taskId': '100', 'taskOrder': 1},
        #     {'taskId': '101', 'taskOrder': 1},
        #     {'taskId': '102', 'taskOrder': 2}]
        self._list_changes = list()
        self._retrieve_tasks()

    def _retrieve_tasks(self):
        """Extract tasks from CVP Server.

        Connect to CVP server and collect tasks in pending state
        These tasks are saved in self._available structure dedicated
        to pending tasks.

        """
        logging.debug('getting list of available task for change control')
        self._available = self._cvp_server.api.change_control_available_tasks()

    def add_task(self, task):
        """Add a tasks to available list.

        This task attach this new tasks to the pending tasks list.

        Parameters
        ----------
        task : str
            TaskID from CVP server

        """
        self._available.append(task)

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
        logging.debug('extractig list of available tasks out of our instance')
        if refresh:
            logging.debug('refreshing list of tasks available for change control')  # noqa E501
            self._retrieve_tasks()
        return self._available

    def _build_change_dictionnary(self, order_mode='linear'):
        """Build ordered list to schedule changes.

        CVP Change Control expect a list with an order to run tasks.
        By default, all tasks are executed at the same time.
        But using order_mode set to incremental every task will
        be scheduled sequentially in this change-control

        Parameters
        ----------
        order_mode : str
            Optional - Method to build task list.
            Shall be ``linear`` or ``incremental``.

        Note
        ----
        Only linear has been tested.

        """
        logging.info('Building a dictionary of changes')
        change_position = 1
        for task in self._available:
            change = dict()
            change['taskId'] = task['workOrderId']
            change['taskOrder'] = (change_position)
            logging.debug('  > Adding task %s to position %s',
                          change['taskId'],
                          change['taskOrder'])
            self._list_changes.append(change)
            if order_mode == 'incremental':
                change_position += 1

    def get_list_changes(self, mode='linear'):
        """Return list of tasks and their execution order.

        Parameters
        ----------
        mode : str
            Information about tasks scheduling.
            Shall be ``linear`` or ``incremental``.

        Note
        ----
        Only linear has been tested.

        Returns
        -------
        list
            List of changes and their order

        """
        if len(self._list_changes) == 0:
            self._build_change_dictionnary(order_mode=mode)
        return self._list_changes

    # TODO: manage way to retrieve Template ID
    def create(self, mode='linear',
               country='France',
               tz='Europe/Paris',
               schedule=False,
               schedule_at='',
               snap_template='1708dd89-ff4b-4d1e-b09e-ee490b3e27f0',
               change_type='Custom',
               stop_on_error="true"):
        """Create a change-control.

        Parameters
        ----------
        mode : str
            Optional - method to order tasks (default : linear)
        country : str
            Optional - Country requested by CVP API (default:France)
        tz : str
            Optional - Timezone required by CVP (default: Europe/Paris)
        schedule : bool
            Optional - Enable CC scheduling (default: False)
        schedule_at : str
            Optional - Time to execute CC if scheduled
        snap_template : str
            Optional - Snapshot template ID to run before / after tasks
        change_type : str
            Optional - CVP definition for CC Might be Custom or Rollback.
            (default: Custom)
        stop_on_error : str
            Optional - boolean string to stop CVP on errors

        Returns
        -------
        dict
            CVP creation result (None if error occurs)

        """
        # If scheduling is not enable, then we create cahnge control
        # to be run now+3 minutes by default
        if schedule is False:
            schedule_at = (datetime.now() + timedelta(seconds=180)).strftime("%Y-%m-%d %H:%M")  # noqa E501
            logging.debug('configure execution time in +3 minutes (%s)',
                          schedule_at)

        # If list of changes to apply hsa not been built already,
        # then we do it before creating change request
        if len(self._list_changes) == 0:
            self._build_change_dictionnary(order_mode=mode)

        logging.debug('Tasks to attach to current change-control:')
        for entry in self._list_changes:
            logging.debug('  * Found task %s w/ position %s',
                          entry['taskId'],
                          entry['taskOrder'])
        # FIXME: change-control does not set snapshot ID correctly and this one is not run before and after change
        # Fix implemented in develop version :
        # https://github.com/aristanetworks/cvprac/blob/develop/cvprac/cvp_api.py#L1633
        # pip install pip install git+https://github.com/aristanetworks/cvprac.git@develop
        # Should solve problem
        try:
            creation_request = self._cvp_server.api.create_change_control(name=self._name,   # noqa E501
                change_control_tasks=self._list_changes,
                timezone=tz,
                country_id=country,
                date_time=schedule_at,
                snapshot_template_key=snap_template,
                change_control_type=change_type,
                stop_on_error=stop_on_error)
            return creation_request
        except CvpApiError as err:
            logging.error('Cannot create change-control - error message is %s',
                          format(err))
            return None
