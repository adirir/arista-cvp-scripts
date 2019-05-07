from cvprac.cvp_client import CvpClient


class CvpInventory(object):
    """CVP Inventory Class.

    Get complete inventory from CVP and expose some functions to get data.
    It is RO only and nothing is pushed to CVP with this object.

    """

    def __init__(self, cvp_server=CvpClient()):
        """Class Constructor.

        Instantiate an Inventory with a REST call to get device list

        Parameters
        ----------
        cvp_server : cvprack.CvpClient()
            Your CVP Rack server

        """
        self._cvp_server = cvp_server
        self._inventory = self._cvp_server.api.get_inventory()

    def get_device_dict(self, name):
        """Get information for a given device.

        Parameters
        ----------
        ``name``: str
            Hostname to lookup

        Returns
        -------
        dict:
            Complete dictionnary sent by CVP

        """
        for device in self._inventory:
            if device['hostname'] == name:
                return device
        return None

    def get_devices(self):
        """Give a dict of all devices.

        Returns
        -------
        dict: All devices attached to CVP inventory

        """
        return self._inventory
