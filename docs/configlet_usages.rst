How to use configilet uploader
==============================


Script can be use to manage configlet on a CloudVision (CVP) server

To manage all actions to run on a CVP server is by using a JSON file to list a set of actions. This json file is provided to the script by using ```-json``` trigger on CLI.

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

- Create a configlet
- Update content of a configlet
- Delete a configlet from Cloud Vision Portal
- Add a device to an existing configlet
- Remove a device from an existing configlet

.. note::
    For the first 2 options, a local content for any configlet shall be present to push content to Cloud Vision. In other scenario, only the name of the configlet targetting by your action should be defined.


Create a configlet with add task
--------------------------------

To create a new configlet on CVP server, ``JSON`` file shall have the following structure:

.. code:: json

  {
      "name": "new CVP Configlet",
      "type": "configlet",
      "action": "add",
      "configlet": "configlet.examples/VLANsTEMP",
      "apply": false,
      "devices": [
          "leaf1",
          "leaf2",
          "leaf3"
      ]
  }

Where **keys** have description below:

- ``name``: A name for the task. it is only a local name and it is not used on CVP side.
- ``type``: shall be **configlet**. It define what kind of entry to manage on CVP. in this case, we are talking about a configlet.
- ``action``: Action to run on configlet. As we want to create a new one, action shall be **add**
- ``configlet``: Path to the configlet. Remember that file name will be used as configlet name.
- ``apply``: define wether or not we should deploy this configlet to devices. if set to **false**, then a change-control or manual action should be done later.
- ``devices``: An array of devices hostname configured on CVP where to attache configlet.


Update content of a configlet with update task
----------------------------------------------

To update an existing configlet on CVP server, ``JSON`` file shall have the following structure:

.. code:: json

  {
      "name": "new CVP Configlet",
      "type": "configlet",
      "action": "update",
      "configlet": "configlet.examples/VLANs",
      "apply": true
  }

Where **keys** have description below:

- ``name``: A name for the task. it is only a local name and it is not used on CVP side.
- ``type``: shall be **configlet**. It define what kind of entry to manage on CVP. in this case, we are talking about a configlet.
- ``action``: Action to run on configlet. As we want to create a new one, action shall be **update**
- ``configlet``: Path to the configlet. Remember that file name will be used as configlet name.
- ``apply``: define wether or not we should deploy this configlet to devices. if set to **false**, then a change-control or manual action should be done later.
- ``devices``: An array of devices hostname configured on CVP where to attache configlet.

.. note:: *Note:* If configlet is not already configured on your CloudVision server, then script try to create it. Creation requires a list devices configured in this specific task.


Delete a configlet with delete task
-----------------------------------

To delete an existing configlet on CVP server, ``JSON`` file shall have the following structure:

.. code:: json

  {
      "name": "new CVP Configlet",
      "type": "configlet",
      "action": "delete",
      "configlet": "configlet.examples/VLANsTEMP",
      "apply": true
  }

Where **keys** have description below:

- ``name``: A name for the task. it is only a local name and it is not used on CVP side.
- ``type``: shall be **configlet**. It define what kind of entry to manage on CVP. in this case, we are talking about a configlet.
- ``action``: Action to run on configlet. As we want to create a new one, action shall be **delete**
- ``configlet``: Path to the configlet. Remember that file name will be used as configlet name.
- ``apply``: define wether or not we should deploy this configlet to devices. if set to **false**, then a change-control or manual action should be done later.
- ``devices``: An array of devices hostname configured on CVP where to attache configlet.

Remove a device from configlet with remove-device task
------------------------------------------------------

To remove a device from a configlet on CVP server, ``JSON`` file shall have the following structure:

.. code:: json

  {
      "name": "new CVP Configlet",
      "type": "configlet",
      "action": "remove-devices",
      "configlet": "configlet.examples/VLANsTEMP",
      "apply": false,
      "devices": [
          "leaf3"
      ]
  }

Where **keys** have description below:

- ``name``: A name for the task. it is only a local name and it is not used on CVP side.
- ``type``: shall be **configlet**. It define what kind of entry to manage on CVP. in this case, we are talking about a configlet.
- ``action``: Action to run on configlet. As we want to create a new one, action shall be **remove-devices**
- ``configlet``: Path to the configlet. Remember that file name will be used as configlet name.
- ``apply``: define wether or not we should deploy this configlet to devices. if set to **false**, then a change-control or manual action should be done later.
- ``devices``: An array of devices hostname to remove from the configlet.

Attach device to a configlet with add-device task
-------------------------------------------------

To attach a device or a list of devices to a configlet on CVP server, ``JSON`` file shall have the following structure:

.. code:: json

  {
      "name": "new CVP Configlet",
      "type": "configlet",
      "action": "add-devices",
      "configlet": "configlet.examples/VLANsTEMP",
      "apply": false,
      "devices": [
          "leaf3",
          "leaf1"
      ]
  }

Where **keys** have description below:

- ``name``: A name for the task. it is only a local name and it is not used on CVP side.
- ``type``: shall be **configlet**. It define what kind of entry to manage on CVP. in this case, we are talking about a configlet.
- ``action``: Action to run on configlet. As we want to create a new one, action shall be **add-devices**
- ``configlet``: Path to the configlet. Remember that file name will be used as configlet name.
- ``apply``: define wether or not we should deploy this configlet to devices. if set to **false**, then a change-control or manual action should be done later.
- ``devices``: An array of devices hostname to remove from the configlet.


Change-control building
-----------------------

To delete an existing configlet on CVP server, ``JSON`` file shall have the following structure:

.. code:: json

    {
        "name": "Change Control to deploy last update",
        "type": "change-control",
        "schedule": "2019-03-15-12-30",
        "snapid": "snapshotTemplate_9_4694793526491",
        "apply": true,
    },

Where **keys** have description below:

- ``name``: A name for the task. it is only a local name and it is not used on CVP side.
- ``type``: shall be **change-control**. It define what kind of entry to manage on CVP. in this case, we are talking about a change-control.
- ``schedule``:  *optional* entry to schedule execution of change control. if not set, change-control is executed 3 minutes after entry registration
- ``apply``: If set to ``true``, then, script will schedule change-control execution using ``schedule`` field or 3 minutes after change-control creation. If set to ``false``, change control must be executed manually.

Some other options are also available for this action:

- ``timezone``: Timezone of the server to manage scheduling. By default, it is set to ``Europe/Paris`` timezone.
- ``country``: Country where CVP is for time managemement as well. By default it is set to ``France``.

.. warning::
    Timezone should be defined according time-zone configured on the machine you are running the script. In the meantime, your Cloud Vision server shall be NTP synced with correct timezone as well.