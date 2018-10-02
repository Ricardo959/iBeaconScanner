# 1. Install: sudo pip3 install bluepy
# 2. Install: sudo pip3 install grequests
# 3. Run: sudo python3 iBeaconScanner.py


from bluepy import btle
from bluepy.btle import DefaultDelegate
import datetime
import grequests
import json


ID = 1
SECONDS = 5 # Scan duration
URL = "https://ibeacon-tracker.herokuapp.com/anchor_tag_detections"
HEADERS = {"Accept":"application/json","Content-Type":"application/json"}
FILTER = ["5c:f8:21", "f3:4f:c8"]
devices = []


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
                              "date_time": str(datetime.datetime.now()),
                              "is_in_range": True}
                    
                    devices.append(device)


# Loop:
while True:
    print("Scanning for %d seconds..." % SECONDS)
    scanner = btle.Scanner().withDelegate(ScanDelegate())
    advertidedDevices = scanner.scan(SECONDS)
    print("Done! Found devices: %d" % len(advertidedDevices))
            
    json = {"anchor_tag_detection": devices}

    print("Matching devices: %d\n\nJSON: %s\n" % (len(devices), json))

    print("Preparing HTTP request...")
    request = grequests.post(URL, json=json, headers=HEADERS)
    print("Status code: %d" % (request.status_code), end=" ")

    if request.status_code == 200:
        print("OK\n")
        devices = []
    else:
        print("Error\n")
