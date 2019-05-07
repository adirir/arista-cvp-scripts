How to use configilet uploader
==============================

Script uses a JSON file to describe list of actions to run on CloudVision server. This json file is provided to the script by using ```-json``` trigger on CLI.

JSON file is an array of entries where every single entry in JSON file describe a task to run:

.. code:: json

  [
    {
        //task 1
    },
    {
        //task 2
    }
  ]

Current version of code support all the actions listed below:

- Create a container in CoudVision topology
- Move a list of devices to an existing container.
- Delete a container from CloudVision topology.

Create a container within CVP Topology:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can create a container in CloudVision topology using a JSON like below.

JSON example:
^^^^^^^^^^^^^

.. code:: json

    {
        "name": "Create container",
        "type": "container",
        "action": "create",
        "container": "Test Container",
        "parent": "Tenant"
    }

Where **keys** have description below:

- ``name``: A name for the task. it is only a local name and it is not used on CVP side.
- ``type``: shall be **container**. It define what kind of entry to manage on CVP. in this case, we are talking about a container.
- ``action``: Action to run on configlet. As we want to attach devices to container, action shall be **creation**
- ``container``: Name of existing container where devices will be attached.
- ``parent``: Name of parent container. It is value you have in your toipology. By default, container will be created under **Tenant**

.. warning::
  This action execute task directly and there is no way to just provisionned and execute action later or manually.

Example outputs:
^^^^^^^^^^^^^^^^

.. code:: shell

  --------------------

  2019-04-30 13:51:51 INFO     creation of container with name Test Container attached to Tenant
  2019-04-30 13:51:52 INFO     Connected to 54.219.174.143
  2019-04-30 13:51:52 INFO     *************
  2019-04-30 13:51:52 INFO     Start working with Test Container
  2019-04-30 13:51:52 INFO     initializing a container object for Test Container
  2019-04-30 13:51:52 INFO     Version [u'2018', u'2', u'2']
  2019-04-30 13:51:52 INFO     Setting API version to v2
  2019-04-30 13:51:54 WARNING  container Test Container not found
  2019-04-30 13:51:54 INFO     create container on CVP server
  2019-04-30 13:51:54 INFO     start creation of container attached to Tenant


Delete a container from CVP Topology:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can delete a container in CloudVision topology using a JSON like below.

JSON example:
^^^^^^^^^^^^^

.. code:: json

    {
        "name": "Create container",
        "type": "container",
        "action": "destroy",
        "container": "Test Container",
        "parent": "Tenant"
    }

Where **keys** have description below:

- ``name``: A name for the task. it is only a local name and it is not used on CVP side.
- ``type``: shall be **container**. It define what kind of entry to manage on CVP. in this case, we are talking about a container.
- ``action``: Action to run on configlet. As we want to attach devices to container, action shall be **destroy**
- ``container``: Name of existing container where devices will be attached.
- ``parent``: Name of parent container. It is value you have in your toipology. By default, container will be created under **Tenant**

.. note::
  To execute this action, your container should not contain any attached device. if some are still attached, process will stop.

.. warning::
  This action execute task directly and there is no way to just provisionned and execute action later or manually.

Example outputs:
^^^^^^^^^^^^^^^^

.. code:: shell

  --------------------

  2019-04-30 14:17:36 INFO     destruction of container with name Test Container
  2019-04-30 14:17:37 INFO     Connected to 54.219.174.143
  2019-04-30 14:17:37 INFO     *************
  2019-04-30 14:17:37 INFO     Start working with Test Container
  2019-04-30 14:17:37 INFO     initializing a container object for Test Container
  2019-04-30 14:17:37 INFO     Version [u'2018', u'2', u'2']
  2019-04-30 14:17:37 INFO     Setting API version to v2
  2019-04-30 14:17:41 INFO     destroy container from CVP server
  2019-04-30 14:17:41 INFO     start process to delete container Test Container


Move devices to an existing container:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Script provides a mechanism to move devices to an existing container. JSON syntax to support such operation is provided below:

JSON example:
^^^^^^^^^^^^^

.. code:: json

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

Where **keys** have description below:

- ``name``: A name for the task. it is only a local name and it is not used on CVP side.
- ``type``: shall be **container**. It define what kind of entry to manage on CVP. in this case, we are talking about a container.
- ``action``: Action to run on configlet. As we want to attach devices to container, action shall be **attach-device**
- ``container``: Name of existing container where devices will be attached.
- ``apply``: define wether or not we should deploy this configlet to devices. if set to **false**, then a change-control or manual action should be done later by user.
- ``devices``: An array of devices hostname configured on CVP to move to ``container``.

Example outputs:
^^^^^^^^^^^^^^^^

.. code:: shell

  --------------------

  2019-04-30 10:21:54 INFO     device leaf1 is going to be moved to CVX
  2019-04-30 10:21:54 INFO     device leaf2 is going to be moved to CVX
  2019-04-30 10:21:54 INFO     device cvx01 is going to be moved to CVX
  2019-04-30 10:21:55 INFO     Connected to 54.219.174.143
  2019-04-30 10:21:55 INFO     *************
  2019-04-30 10:21:55 INFO     Start working with CVX
  2019-04-30 10:21:55 INFO     initializing a container object for CVX
  2019-04-30 10:21:55 INFO     Version [u'2018', u'2', u'2']
  2019-04-30 10:21:55 INFO     Setting API version to v2
  2019-04-30 10:21:59 INFO     check is devices are already part of container
  2019-04-30 10:21:59 INFO     device is not part of that container -- moving forward
  2019-04-30 10:21:59 INFO     device is not part of that container -- moving forward
  2019-04-30 10:21:59 CRITICAL device is already part of that container -- skipping
  2019-04-30 10:21:59 INFO     >---
  2019-04-30 10:21:59 INFO     starting process to attach a list of device to CVX
  2019-04-30 10:21:59 INFO     >---
  2019-04-30 10:21:59 INFO     create change to move leaf1 to CVX
  2019-04-30 10:22:03 INFO     task created on CVP: 250
  2019-04-30 10:22:03 INFO     >---
  2019-04-30 10:22:03 INFO     create change to move leaf2 to CVX
  2019-04-30 10:22:06 INFO     task created on CVP: 251
  2019-04-30 10:22:06 INFO     >---
  2019-04-30 10:22:06 CRITICAL device already attached to CVX
  2019-04-30 10:22:06 INFO     >---
  2019-04-30 10:22:06 INFO     run pending tasks to related to container CVX
  2019-04-30 10:22:06 INFO      -> execute task ID: 250
  2019-04-30 10:22:08 INFO       * Wait for task completion (status: ACTIVE) / waiting for 0 sec
  2019-04-30 10:22:09 INFO       * Wait for task completion (status: ACTIVE) / waiting for 1 sec
  2019-04-30 10:22:10 INFO       * Wait for task completion (status: ACTIVE) / waiting for 2 sec
  2019-04-30 10:22:12 INFO       * Wait for task completion (status: COMPLETED) / waiting for 3 sec
  2019-04-30 10:22:12 INFO      -> task 250 status : COMPLETED
  2019-04-30 10:22:12 INFO      -> execute task ID: 251
  2019-04-30 10:22:13 INFO       * Wait for task completion (status: ACTIVE) / waiting for 0 sec
  2019-04-30 10:22:14 INFO       * Wait for task completion (status: ACTIVE) / waiting for 1 sec
  2019-04-30 10:22:15 INFO       * Wait for task completion (status: ACTIVE) / waiting for 2 sec
  2019-04-30 10:22:17 INFO       * Wait for task completion (status: COMPLETED) / waiting for 3 sec
  2019-04-30 10:22:17 INFO      -> task 251 status : COMPLETED