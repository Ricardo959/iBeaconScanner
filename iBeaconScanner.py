'''
1) Install bluepy:       sudo pip3 install bluepy
2) Install grequests:    sudo pip3 install grequests
3) Run the script:       sudo python3 iBeaconScanner.py
'''

from bluepy import btle
from bluepy.btle import DefaultDelegate
import datetime
import grequests
import json
import copy


ID = 1
SECONDS = 5 # Scan duration
URL = "https://ibeacon-tracker.herokuapp.com/anchor_tag_detections"
HEADERS = {"Accept":"application/json","Content-Type":"application/json"}
FILTER = ["5c:f8:21", "f3:4f:c8"]
devices = []
devicesBefore = []


def rssiInMeter(rssi):
    mpower = -72
    N = 2.0 # Constant depends on envroimental factor (Range: 2.0 - 4.0)
    return int(10 ** ((mpower - rssi)/(10 * N)))


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        # Found a device!
        if isNewDev:
            print("Device: %s\tRSSI: %d dB" % (dev.addr, dev.rssi))

            for filter in FILTER:
                if dev.addr[0:8] == filter:
                    # Seems like this device might be in our interest
                    print("-> Device matching manifacturer!")
                    address = str(dev.addr)
                    address = address.replace(":", "")
                    device = {"anchors_id": ID,
                              "address": address,
                              "distance": rssiInMeter(dev.rssi),
                              "date_time": str(datetime.datetime.now())}

                    devices.append(device)

def exception_handler(request, exeption):
    print("Error: %s\n" % exeption)

# Loop:
while True:
    print("Scanning for %d seconds..." % SECONDS)
    scanner = btle.Scanner().withDelegate(ScanDelegate())
    advertidedDevices = scanner.scan(SECONDS)
    print("Done! Found devices: %d" % len(advertidedDevices))

    # print("\ndev now: %s\n\ndev bef: %s\n" % (devices, devicesBefore))

    # Let's delete what has already been sent before to increase performance during data transfer
    devicesCopy = copy.deepcopy(devices)

    for deviceBefore in devicesBefore:
        deviceIsGone = True

        for device in devices:
            if device["address"] == deviceBefore["address"]:
                deviceIsGone = False

                if "distance" in deviceBefore:
                    if deviceBefore["distance"] == device["distance"]:
                        del device["distance"]
                        del device["date_time"]
                break

        if deviceIsGone:
            goneDevice = {"anchors_id": ID,
                          "address": deviceBefore["address"],
                          "is_in_range": False}

            devices.append(goneDevice)
    # Now 'devices' contains only what needs to be updated
    json = {"anchor_tag_detection": devices}
    print("Matching devices: %d\n\nJSON: %s\n" % (len(devices), json))
    devicesBefore = copy.deepcopy(devicesCopy)

    print("Preparing HTTP request...")
    request = [grequests.post(URL, json=json, headers=HEADERS)]
    grequests.map(request, exception_handler=exception_handler, gtimeout=5)

    devices = []
    print("Done!\n")

