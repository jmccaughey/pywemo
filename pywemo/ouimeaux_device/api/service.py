import logging
from xml.etree import cElementTree as et

import requests

from .xsd import service as serviceParser


log = logging.getLogger(__name__)

REQUEST_TEMPLATE = """
<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
 <s:Body>
  <u:{action} xmlns:u="{service}">
   {args}
  </u:{action}>
 </s:Body>
</s:Envelope>
"""

DEFAULT_SERVICE_XML = """<?xml version="1.0" encoding="utf-8"?>
<scpd xmlns="urn:Belkin:service-1-0">
  <specVersion>
    <major>1</major>
    <minor>0</minor>
  </specVersion>
  <actionList>
    <action>
      <name>SetBinaryState</name>
      <argumentList>
        <argument>
          <retval/>
          <name>BinaryState</name>
          <relatedStateVariable>BinaryState</relatedStateVariable>
          <direction>in</direction>
        </argument>
      </argumentList>
    </action>
    <action>
      <name>GetFriendlyName</name>
      <argumentList>
        <argument>
          <retval/>
          <name>FriendlyName</name>
          <relatedStateVariable>FriendlyName</relatedStateVariable>
          <direction>in</direction>
        </argument>
      </argumentList>
    </action>
    <action>
      <name>GetBinaryState</name>
      <argumentList>
        <argument>
          <retval/>
          <name>BinaryState</name>
          <relatedStateVariable>BinaryState</relatedStateVariable>
          <direction>out</direction>
        </argument>
      </argumentList>
    </action>
  </actionList>
  <serviceStateTable>
    <stateVariable sendEvents="yes">
      <name>BinaryState</name>
      <dataType>string</dataType>
      <defaultValue>0</defaultValue>
    </stateVariable>
    <stateVariable sendEvents="No">
      <name>StateList</name>
      <dataType>list</dataType>
      <defaultValue>0</defaultValue>
    </stateVariable>
    <stateVariable sendEvents="yes">
      <name>URL</name>
      <dataType>string</dataType>
      <defaultValue>0</defaultValue>
    </stateVariable>
  </serviceStateTable>
</scpd>
"""

class Action(object):
    def __init__(self, device, service, action_config):
        self._device = device
        self._action_config = action_config
        self.name = action_config.get_name()
        self.serviceType = service.serviceType
        self.controlURL = service.controlURL
        self.args = {}
        self.headers = {
            'Content-Type': 'text/xml',
            'SOAPACTION': '"%s#%s"' % (self.serviceType, self.name)
        }
        arglist = action_config.get_argumentList()
        if arglist is not None:
            for arg in arglist.get_argument():
                # TODO: Get type instead of setting 0
                self.args[arg.get_name()] = 0

    def __call__(self, **kwargs):
        arglist = '\n'.join('<{0}>{1}</{0}>'.format(arg, value)
                            for arg, value in kwargs.items())
        body = REQUEST_TEMPLATE.format(
            action=self.name,
            service=self.serviceType,
            args=arglist
        )
        for attempt in range(3):
            try:
                response = requests.post(
                    self.controlURL, body.strip(),
                    headers=self.headers, timeout=10)
                d = {}
                for r in et.fromstring(response.content).getchildren()[0].getchildren()[0].getchildren():
                    d[r.tag] = r.text
                return d
            except requests.exceptions.RequestException:
                log.warning(
                    "Error communicating with {}, retry {}".format(
                        self._device.name, attempt))
                self._device.reconnect_with_device()

        log.error(
            "Error communicating with {}. Giving up".format(self._device.name))
        return

    def __repr__(self):
        return "<Action %s(%s)>" % (self.name, ", ".join(self.args))


class Service(object):
    """
    Represents an instance of a service on a device.
    """

    def __init__(self, device, service, base_url):
        self._base_url = base_url.rstrip('/')
        self._config = service
        url = '%s/%s' % (base_url, service.get_SCPDURL().strip('/'))
       	print("service url: " + url)
	xmlString = "" 
	try:
	  xml = requests.get(url, timeout=10)
	  xmlString = xml.content
	except:
	  print("exception requesting " + url)
	  xmlString = DEFAULT_SERVICE_XML
	print(xmlString)
        self.actions = {}
        self._svc_config = serviceParser.parseString(xmlString).actionList
        for action in self._svc_config.get_action():
            act = Action(device, self, action)
            name = action.get_name()
            self.actions[name] = act
            setattr(self, name, act)

    #def __init__(self, device, base_url):
#	self._base_url = base_url.rstrip('/')

    @property
    def hostname(self):
        return self._base_url.split('/')[-1]

    @property
    def controlURL(self):
        return '%s/%s' % (self._base_url,
                          self._config.get_controlURL().strip('/'))

    @property
    def serviceType(self):
        return self._config.get_serviceType()
