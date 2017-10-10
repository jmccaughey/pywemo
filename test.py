#!/usr/bin/env python

import pywemo

devices = pywemo.discover_devices(st = "urn:Belkin:device:**")
print(len(devices))
for device in devices:
  print(device)
  if "Godo" in device.name:
    device.on()

