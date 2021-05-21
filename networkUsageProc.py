import os
import sys
import json
from time import sleep
from importlib import import_module
from helper import bold_str, sprintf, cursorUpLines, setupFiles

# Default configuration file
dfltCfgFile = "config_dflt.py"

# Import default configuration file.
# Not using `import config_dflt` because of printing option (`networkUsageProc.py -s`)
# and we want to have only one instance of default config file name - `dfltCfgFile`
config_dflt = import_module(dfltCfgFile.replace(".py", ""))


def displayHelp():
    print("""\
Script to monitor network usage.

Tested with python 3.9.5.

python networkUsageProc.py [OPTIONS]

Options:
  -h, --help        show this help

  -f, --file        json file location - OPTIONAL
                    If this parameter is not specified the file is located
                    at './logs/networkUsage.json' (relative to this script location).

  -p, --print       print network usage to the terminal also - OPTIONAL

  -u, --interval    update interval in seconds - OPTIONAL
                    Interval at which network usage is updated.
                    Defaults to 1 second.

  -i, --interfaces  interfaces to monitor - OPTIONAL
                    Full or partial (Regular Expression) interface name.
                    For multiple interfaces separate them with comma (without space).
                    Example: -i 'eth0:,wl*'
                             -i 'eth0:','wl*'

  -c, --config      custom configuration file - OPTIONAL
                    For example take a look at 'config_dflt.py' or
                    pass '-s' to script to print 'config_dflt.py' to terminal.

  -s, --show        print default configuration file to the terminal
""")


# https://www.tutorialspoint.com/python/python_command_line_arguments.htm
# Ignore "C901 'checkArgs' is too complex" - I don't think that it is too complex, also
# I don't know how mccabe's complexity could be reduced for this function
def checkArgs(networkUsageParam, argv):  # noqa: C901
    import getopt

    shortopts = "hf:pu:i:c:s"
    longopts = [
        "help",
        "file=",
        "print",
        "interval=",
        "interfaces=",
        "config=",
        "show"
    ]

    try:
        opts, args = getopt.getopt(argv, shortopts, longopts)
    except getopt.GetoptError:
        displayHelp()
        sys.exit(1)

    for opt, arg in opts:
        if opt in ('-h', "--help"):
            displayHelp()
            sys.exit(0)
        elif opt in ("-f", "--file"):
            networkUsageParam["networkUsageFile"] = arg
        elif opt in ("-p", "--print"):
            networkUsageParam["printUsageToTerminal"] = True
        elif opt in ("-u", "--interval"):
            networkUsageParam["updateInterval"] = float(arg)
        elif opt in ("-i", "--interfaces"):
            # "wl*","enp*","eth?:"
            networkUsageParam["desiredInterfaces"] = arg.split(",")
        elif opt in ("-c", "--config"):
            # import configuration file
            importConfigModule(arg, networkUsageParam)
        elif opt in ("-s", "--show"):
            printDfltCfgFile()


def printDfltCfgFile():
    with open(dfltCfgFile, "r") as file:
        print(file.read())
        sys.exit(0)


def importConfigModule(moduleName, networkUsageParam):
    moduleName = moduleName.replace(".py", "")
    networkUsageConfig = import_module(moduleName)

    try:
        networkUsageParam["networkUsageFile"] = networkUsageConfig.networkUsageFile
    except AttributeError:
        pass
    try:
        networkUsageParam["printUsageToTerminal"] = networkUsageConfig.printUsageToTerminal
    except AttributeError:
        pass
    try:
        networkUsageParam["updateInterval"] = networkUsageConfig.updateInterval
    except AttributeError:
        pass
    try:
        networkUsageParam["desiredInterfaces"] = networkUsageConfig.desiredInterfaces
    except AttributeError:
        pass


def renderNetworkSpeed(byps):
    if byps >= 10 ** 9:
        return sprintf("%0.2f GB", byps / (10 ** 9))
    elif byps >= 10 ** 6:
        return sprintf("%0.2f MB", byps / (10 ** 6))
    else:
        return sprintf("%0.2f kB", byps / (10 ** 3))


class networkUsageClass:
    def __init__(self,
                 desiredInterfaces=config_dflt.desiredInterfaces,
                 updateInterval=config_dflt.updateInterval,
                 networkUsageFile=config_dflt.networkUsageFile,
                 printUsageToTerminal=config_dflt.printUsageToTerminal):
        # Used to select which interfaces to monitor.
        self.desiredInterfaces = desiredInterfaces

        # Update interval in seconds
        self.updateInterval = updateInterval

        # Where to save current network usage json file
        self.networkUsageFile = networkUsageFile

        # Print network usage to terminal also (not just to json file)
        self.printUsageToTerminal = printUsageToTerminal

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
        # - previously used bytes by interface (byRx_prev, byTx_prev),
        # - current network usage (bypsRx, bypsTx).
        self.selectedInterfaces = []

        # Store current network usage of all interfaces
        self.totalUsage = {"bypsRx": 0, "bypsTx": 0}

        # Setup parent folders of files in filesToSetup array
        setupFiles(self.filesToSetup)

        # Get all the available interfaces, filter available interfaces to only the ones which we
        # desire then setup commands to get bytes used by each interface and get starting bytes
        availableInterfaces = self.getAvailableInterfaces()
        self.filterDesiredInterfaces(availableInterfaces)

        self.numbOfMonitoringInterfaces = len(self.selectedInterfaces)

        self.printConfig()

        if self.numbOfMonitoringInterfaces <= 0:
            print("No interfaces selected!")
            sys.exit(1)
        self.setupInterfaces()

    def printConfig(self):
        print(bold_str("Json file") + ": " + self.networkUsageFile)
        print(bold_str("Printing to terminal") + ": " + str(self.printUsageToTerminal))
        print(bold_str("Update interval") + ": " + str(self.updateInterval))
        print(bold_str("Desired interfaces to monitor") + ": " + str(self.desiredInterfaces))
        for i in range(self.numbOfMonitoringInterfaces):
            if i == 0:
                print(bold_str("Monitoring interfaces") + ": - " + self.selectedInterfaces[i]["name"])
            else:
                print("                       - " + self.selectedInterfaces[i]["name"])

    # Get new bytes used by specified interface
    def getBytes(self, interface):
        byRx = int(os.popen(interface["cmd_getRxBytes"]).read())
        byTx = int(os.popen(interface["cmd_getTxBytes"]).read())
        return byRx, byTx

    # Store new bytes used by specified interface
    def storeFreshBytes(self, interface, byRx, byTx):
        interface["byRx_prev"] = byRx
        interface["byTx_prev"] = byTx

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
                    self.selectedInterfaces.append({"name": availableInterface,
                                                    "bypsRx": 0,
                                                    "bypsTx": 0})

    # Setup interfaces (prepare commands used to get RX and TX bytes,
    # get starting RX and TX bytes)
    def setupInterfaces(self):
        for interface in self.selectedInterfaces:
            interface["cmd_getRxBytes"] = sprintf(self.cmd_getRxBytes, interface["name"])
            interface["cmd_getTxBytes"] = sprintf(self.cmd_getTxBytes, interface["name"])

            byRx, byTx = self.getBytes(interface)
            self.storeFreshBytes(interface, byRx, byTx)

    # Print network usage by specified interface in kB
    def printUsage(self):
        for interface in self.selectedInterfaces:
            print(sprintf("%s - Rx: %s, Tx: %s",
                          interface["name"],
                          renderNetworkSpeed(interface["bypsRx"]),
                          renderNetworkSpeed(interface["bypsTx"])))

        print(sprintf("%s - Rx: %s, Tx: %s",
                      "total",
                      renderNetworkSpeed(self.totalUsage["bypsRx"]),
                      renderNetworkSpeed(self.totalUsage["bypsTx"])))

    # Store interfaces to json file
    # Also add usage by all interfaces - { "name": "total", "bypsRx": 100, "bypsTx": 100 }
    def storeToFile(self):
        jsonFileData = []

        for interface in self.selectedInterfaces:
            jsonFileData.append({
                "name": interface["name"],
                "bypsRx": interface["bypsRx"],
                "bypsTx": interface["bypsTx"],
            })

        jsonFileData.append({
            "name": "total",
            "bypsRx": self.totalUsage["bypsRx"],
            "bypsTx": self.totalUsage["bypsTx"],
        })

        with open(self.networkUsageFile, "w") as file:
            file.write(json.dumps(jsonFileData))

    # Monitor network usage
    # - loop through all interfaces
    # - store to json file
    # - sleep until the next measurement
    def monitorNetworkUsage(self):
        if self.printUsageToTerminal is True:
            print(bold_str("Network usage") + ":")
            self.printUsage()

        while True:
            self.totalUsage["bypsRx"] = 0
            self.totalUsage["bypsTx"] = 0

            for interface in self.selectedInterfaces:
                byRx, byTx = self.getBytes(interface)
                interface["bypsRx"] = round((byRx - interface["byRx_prev"]) / self.updateInterval)
                interface["bypsTx"] = round((byTx - interface["byTx_prev"]) / self.updateInterval)
                self.storeFreshBytes(interface, byRx, byTx)

                self.totalUsage["bypsRx"] += interface["bypsRx"]
                self.totalUsage["bypsTx"] += interface["bypsTx"]

            self.storeToFile()

            if self.printUsageToTerminal is True:
                cursorUpLines(self.numbOfMonitoringInterfaces + 1)
                self.printUsage()

            sleep(self.updateInterval)


# Start networkUsage script
# - check that all files can be opened/created (check file path)
# - get all the available interfaces to monitor
# - filter available interfaces to select only the desired ones
# - setup interfaces (prepare commands, make first measurement/monitoring...)
# - monitor network usage
def main():
    networkUsageParam = {}
    networkUsageParam["desiredInterfaces"] = config_dflt.desiredInterfaces
    networkUsageParam["updateInterval"] = config_dflt.updateInterval
    networkUsageParam["networkUsageFile"] = config_dflt.networkUsageFile
    networkUsageParam["printUsageToTerminal"] = config_dflt.printUsageToTerminal

    if len(sys.argv) > 1:
        checkArgs(networkUsageParam, sys.argv[1:])

    networkUsage = networkUsageClass(
        desiredInterfaces=networkUsageParam["desiredInterfaces"],
        updateInterval=networkUsageParam["updateInterval"],
        networkUsageFile=networkUsageParam["networkUsageFile"],
        printUsageToTerminal=networkUsageParam["printUsageToTerminal"])
    networkUsage.monitorNetworkUsage()


if __name__ == "__main__":
    main()
