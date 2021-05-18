import os
import json
from time import sleep

# Used to select which interfaces to monitor.
# Full or partial (Regular Expression) interface names.
desiredInterfaces = [
    "wl*",
    "enp*",
    "eth?:",
]

# Where to save current network usage json file
networkUsageFile_dflt = os.path.dirname(os.path.abspath(__file__)) + "/logs/networkUsage.json"

# Array of files (full path) which are checked at setup
# Needed in case some parent folder doesn't exists
filesToSetup = [
    networkUsageFile_dflt,
]

# Command which is used to get RX bytes for specific interface
cmd_getRxBytes = "cat /sys/class/net/%s/statistics/rx_bytes"

# Command which is used to get TX bytes for specific interface
cmd_getTxBytes = "cat /sys/class/net/%s/statistics/tx_bytes"

# Command which is used to get all available interfaces
cmd_getAvailableInterfaces = "cat /proc/net/dev | grep : | awk '{printf(\"%s\\n\", $1)}' | sed 's/://g'"


# C like sprintf function
def sprintf(format, *args):
    return (format % args)


# Check if file path exists, if it doesn't create it
def setupFiles(files):
    for file in files:
        directory = os.path.dirname(file)
        if not os.path.exists(directory):
            os.makedirs(directory)


# Get new bytes used by specified interface
def getBytes(interface):
    interface["byRx_curr"] = int(os.popen(interface["cmd_getRxBytes"]).read())
    interface["byTx_curr"] = int(os.popen(interface["cmd_getTxBytes"]).read())


# Store new bytes used by specified interface
def storeFreshBytes(interface):
    interface["byRx_prev"] = interface["byRx_curr"]
    interface["byTx_prev"] = interface["byTx_curr"]


# Get all available interface
# Return available interfaces
def getAvailableInterfaces():
    interfaces = os.popen(cmd_getAvailableInterfaces).read().splitlines()
    return interfaces


# From all available interfaces filter only desired one
# Return filtered/selected interfaces (in json format)
def filterDesiredInterfaces(availableInterfaces, desiredInterfaces):
    import re

    selectedInterfaces = []

    for availableInterface in availableInterfaces:
        for desiredInterface in desiredInterfaces:
            pattern = re.compile(desiredInterface)
            if pattern.match(availableInterface):
                selectedInterfaces.append({ "name": availableInterface })

    return selectedInterfaces


# Setup interfaces array for usage (prepare command used to get RX and TX bytes,
# get current RX and TX bytes)
def setupInterfaces(interfaces):
    for interface in interfaces:
        interface["cmd_getRxBytes"] = sprintf(cmd_getRxBytes, interface["name"])
        interface["cmd_getTxBytes"] = sprintf(cmd_getTxBytes, interface["name"])

        getBytes(interface)
        storeFreshBytes(interface)


# Print network usage by specified interface in kB
def printUsage(interface):
    print(sprintf("%s - Rx: %d kB, Tx: %d kB",
                  interface["name"],
                  interface["bypsRx"]/1000,
                  interface["bypsTx"]/1000))


# Store interfaces to json file
# Also add usage by all interfaces - { "name": "total", "bypsRx": 100, "bypsTx": 100 }
def storeToFile(interfaces, jsonFile):
    totalUsage = {
        "name": "total",
        "bypsRx": 0,
        "bypsTx": 0,
    }

    jsonFileData = []

    for interface in interfaces:
        totalUsage["bypsRx"] += interface["bypsRx"]
        totalUsage["bypsTx"] += interface["bypsTx"]
        jsonFileData.append({
            "name": interface["name"],
            "bypsRx": interface["bypsRx"],
            "bypsTx": interface["bypsTx"],
        })


    jsonFileData.append({
        "name": totalUsage["name"],
        "bypsRx": totalUsage["bypsRx"],
        "bypsTx": totalUsage["bypsTx"],
    })

    with open(jsonFile, "w") as file:
        file.write(json.dumps(jsonFileData))


# Monitor network usage
# - loop through all interfaces
# - store to json file
# - sleep until the next measurement
def monitorNetworkUsage(selectedInterfaces):
    while True:
        for interface in selectedInterfaces:
            getBytes(interface)
            interface["bypsRx"] = interface["byRx_curr"] - interface["byRx_prev"]
            interface["bypsTx"] = interface["byTx_curr"] - interface["byTx_prev"]
            # print(interface["name"] + "  RX: " + str(interface["bypsRx"]/1000) + " TX: " + str(interface["bypsTx"]/1000))
            # print(interface["name"] + "  RX: " + str(interface["byRx"]) + " TX: " + str(interface["byTx"]))
            # printUsage(interface)
            storeFreshBytes(interface)

        storeToFile(selectedInterfaces, networkUsageFile_dflt)

        sleep(1)



# Start networkUsage script
# - check that all files can be opened/created (check file path)
# - get all the available interfaces to monitor
# - filter available interfaces to select only the desired ones
# - setup interfaces (prepare commands, make first measurement/monitoring...)
# - monitor network usage
def startMonitor():
    setupFiles(filesToSetup)

    availableInterfaces = getAvailableInterfaces()
    selectedInterfaces = filterDesiredInterfaces(availableInterfaces, desiredInterfaces)
    setupInterfaces(selectedInterfaces)

    monitorNetworkUsage(selectedInterfaces)


if __name__ == "__main__":
    startMonitor()

