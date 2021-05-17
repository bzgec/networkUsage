import os
from time import sleep

desiredInterfaces = [
    "wl*",
    "enp*",
    "eth?:",
]

cpuTemperatureFile = os.path.dirname(os.path.abspath(__file__)) + "/logs/networkUsage.json"

cmd_getTxBytes = "cat /sys/class/net/%s/statistics/tx_bytes"
cmd_getRxBytes = "cat /sys/class/net/%s/statistics/rx_bytes"

cmd_getAvailableInterfaces = "cat /proc/net/dev | grep : | awk '{printf(\"%s\\n\", $1)}' | sed 's/://g'"


def sprintf(format, *args):
    return (format % args)


def getBytes(interface):
    interface["byRx_curr"] = int(os.popen(interface["cmd_getRxBytes"]).read())
    interface["byTx_curr"] = int(os.popen(interface["cmd_getTxBytes"]).read())


def storeFreshBytes(interface):
    interface["byRx_prev"] = interface["byRx_curr"]
    interface["byTx_prev"] = interface["byTx_curr"]


def getAvailableInterfaces():
    interfaces = os.popen(cmd_getAvailableInterfaces).read().splitlines()
    return interfaces


def filterDesiredInterfaces(availableInterfaces, desiredInterfaces):
    import re

    selectedInterfaces = []

    for availableInterface in availableInterfaces:
        for desiredInterface in desiredInterfaces:
            pattern = re.compile(desiredInterface)
            if pattern.match(availableInterface):
                selectedInterfaces.append({ "name": availableInterface })

    return selectedInterfaces


def setupInterfaces(interfaces):
    for interface in interfaces:
        interface["cmd_getRxBytes"] = sprintf(cmd_getRxBytes, interface["name"])
        interface["cmd_getTxBytes"] = sprintf(cmd_getTxBytes, interface["name"])

        getBytes(interface)
        storeFreshBytes(interface)


def printUsage(interface):
    print(sprintf("%s - Rx: %d kB, Tx: %d kB", interface["name"], interface["bypsRx"]/1000, interface["bypsTx"]/1000))


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
        file.write(str(jsonFileData))


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

        storeToFile(selectedInterfaces, cpuTemperatureFile)

        sleep(1)


def startMonitor():
    availableInterfaces = getAvailableInterfaces()
    selectedInterfaces = filterDesiredInterfaces(availableInterfaces, desiredInterfaces)
    setupInterfaces(selectedInterfaces)

    monitorNetworkUsage(selectedInterfaces)


if __name__ == "__main__":
    startMonitor()

