import os
import json
from time import sleep
import config_dflt


# C like sprintf function
def sprintf(format, *args):
    return (format % args)


# Check if file path exists, if it doesn't create it
def setupFiles(files):
    for file in files:
        directory = os.path.dirname(file)
        if not os.path.exists(directory):
            os.makedirs(directory)


class networkUsageClass:
    def __init__(self, parameters):
        # Used to select which interfaces to monitor.
        self.desiredInterfaces = parameters.desiredInterfaces

        # Update interval in seconds
        self.updateInterval = parameters.updateInterval

        # Where to save current network usage json file
        self.networkUsageFile = parameters.networkUsageFile

        # Array of files (full path) which are checked at setup
        # Needed in case some parent folder doesn't exists
        self.filesToSetup = [
            self.networkUsageFile,
        ]

        # Command which is used to get RX bytes for specific interface
        self.cmd_getRxBytes = "cat /sys/class/net/%s/statistics/rx_bytes"

        # Command which is used to get TX bytes for specific interface
        self.cmd_getTxBytes = "cat /sys/class/net/%s/statistics/tx_bytes"

        # Command which is used to get all available interfaces
        self.cmd_getAvailableInterfaces = "cat /proc/net/dev | grep : | awk '{printf(\"%s\\n\", $1)}' | sed 's/://g'"

        # Array which is going to hold:
        # - names of interfaces,
        # - commands to get current bytes (cmd_getRxBytes, cmd_getTxBytes),
        # - current bytes used by interface (byRx_curr, byTx_curr),
        # - previously used bytes by interface (byRx_prev, byTx_prev),
        # - current network usage (bypsRx, bypsTx).
        self.selectedInterfaces = []

        # Setup parent folders of files in filesToSetup array
        setupFiles(self.filesToSetup)

        # Get all the available interfaces, filter available interfaces to only the ones which we
        # desire then setup commands to get bytes used by each interface and get starting bytes
        availableInterfaces = self.getAvailableInterfaces()
        self.filterDesiredInterfaces(availableInterfaces)
        self.setupInterfaces()

    # Get new bytes used by specified interface
    def getBytes(self, interface):
        interface["byRx_curr"] = int(os.popen(interface["cmd_getRxBytes"]).read())
        interface["byTx_curr"] = int(os.popen(interface["cmd_getTxBytes"]).read())

    # Store new bytes used by specified interface
    def storeFreshBytes(self, interface):
        interface["byRx_prev"] = interface["byRx_curr"]
        interface["byTx_prev"] = interface["byTx_curr"]

    # Get all available interface
    # Return available interfaces
    def getAvailableInterfaces(self):
        interfaces = os.popen(self.cmd_getAvailableInterfaces).read().splitlines()
        return interfaces

    # From all available interfaces filter only desired one
    # Return filtered/selected interfaces (in json format)
    def filterDesiredInterfaces(self, availableInterfaces):
        import re

        for availableInterface in availableInterfaces:
            for desiredInterface in self.desiredInterfaces:
                pattern = re.compile(desiredInterface)
                if pattern.match(availableInterface):
                    self.selectedInterfaces.append({"name": availableInterface})

    # Setup interfaces (prepare commands used to get RX and TX bytes,
    # get starting RX and TX bytes)
    def setupInterfaces(self):
        for interface in self.selectedInterfaces:
            interface["cmd_getRxBytes"] = sprintf(self.cmd_getRxBytes, interface["name"])
            interface["cmd_getTxBytes"] = sprintf(self.cmd_getTxBytes, interface["name"])

            self.getBytes(interface)
            self.storeFreshBytes(interface)

    # Print network usage by specified interface in kB
    def printUsage(interface):
        print(sprintf("%s - Rx: %d kB, Tx: %d kB",
                      interface["name"],
                      interface["bypsRx"] / 1000,
                      interface["bypsTx"] / 1000))

    # Store interfaces to json file
    # Also add usage by all interfaces - { "name": "total", "bypsRx": 100, "bypsTx": 100 }
    def storeToFile(self):
        totalUsage = {
            "name": "total",
            "bypsRx": 0,
            "bypsTx": 0,
        }

        jsonFileData = []

        for interface in self.selectedInterfaces:
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

        with open(self.networkUsageFile, "w") as file:
            file.write(json.dumps(jsonFileData))

    # Monitor network usage
    # - loop through all interfaces
    # - store to json file
    # - sleep until the next measurement
    def monitorNetworkUsage(self):
        while True:
            for interface in self.selectedInterfaces:
                self.getBytes(interface)
                interface["bypsRx"] = interface["byRx_curr"] - interface["byRx_prev"]
                interface["bypsTx"] = interface["byTx_curr"] - interface["byTx_prev"]
                self.storeFreshBytes(interface)

            self.storeToFile()

            sleep(self.updateInterval)


# Start networkUsage script
# - check that all files can be opened/created (check file path)
# - get all the available interfaces to monitor
# - filter available interfaces to select only the desired ones
# - setup interfaces (prepare commands, make first measurement/monitoring...)
# - monitor network usage
def main():
    networkUsage = networkUsageClass(config_dflt)
    networkUsage.monitorNetworkUsage()


if __name__ == "__main__":
    main()
