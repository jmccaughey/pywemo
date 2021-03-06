"""
Module to discover WeMo devices.
"""
import requests

from . import ssdp
from .ouimeaux_device.bridge import Bridge
from .ouimeaux_device.insight import Insight
from .ouimeaux_device.lightswitch import LightSwitch
from .ouimeaux_device.motion import Motion
from .ouimeaux_device.switch import Switch
from .ouimeaux_device.maker import Maker
from .ouimeaux_device.coffeemaker import CoffeeMaker
from .ouimeaux_device.api.xsd import device as deviceParser


def discover_devices(st=None, max_devices=None, match_mac=None):
    """ Finds WeMo devices on the local network. """
    print("in discover_devices...")
    st = st or ssdp.ST_ROOTDEVICE
    print("hi")
    ssdp_entries = ssdp.scan(st, max_entries=max_devices, match_mac=match_mac)
    print("returned from ssdp.scan")
    wemos = []
    print(len(ssdp_entries))
    for entry in ssdp_entries:
 	print("yo")
        if entry.match_device_description(
                {'manufacturer': 'Belkin International Inc.'}):
	    print("does match desc")
            mac = entry.description.get('device').get('macAddress')
            device = device_from_description(entry.location, mac)

            if device is not None:
                wemos.append(device)
	else:
	    print("does not match desc")

    return wemos


def device_from_description(description_url, mac):
    """ Returns object representing WeMo device running at host, else None. """
    xml = requests.get(description_url, timeout=10)
    uuid = deviceParser.parseString(xml.content).device.UDN
    return device_from_uuid_and_location(uuid, mac, description_url)


def device_from_uuid_and_location(uuid, mac, location):
    """ Tries to determine which device it is based on the uuid. """
    if uuid is None:
        return None
    elif uuid.startswith('uuid:Socket'):
        return Switch(location, mac)
    elif uuid.startswith('uuid:Lightswitch'):
        return LightSwitch(location, mac)
    elif uuid.startswith('uuid:Insight'):
        return Insight(location, mac)
    elif uuid.startswith('uuid:Sensor'):
        return Motion(location, mac)
    elif uuid.startswith('uuid:Maker'):
        return Maker(location, mac)
    elif uuid.startswith('uuid:Bridge'):
        return Bridge(location, mac)
    elif uuid.startswith('uuid:CoffeeMaker'):
        return CoffeeMaker(location, mac)
    else:
        return None
