import os

# Used to select which interfaces to monitor.
# Full or partial (Regular Expression) interface names.
desiredInterfaces = [
    "wl*",
    "enp*",
    "eth?:",
]

# Update interval in seconds
updateInterval = 1

# Where to save current network usage json file
networkUsageFile = os.path.dirname(os.path.abspath(__file__)) + "/logs/networkUsage.json"

# Print network usage to the terminal also (not just to the json file)
printUsageToTerminal = False
