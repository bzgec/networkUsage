import os
import sys


class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def bold_str(str):
    return (color.BOLD + str + color.END)


# Check if file path exists, if it doesn't create it
def setupFiles(files):
    for file in files:
        directory = os.path.dirname(file)
        if not os.path.exists(directory) and directory != "" and directory != ".":
            os.makedirs(directory)


# C like sprintf function
def sprintf(format, *args):
    return (format % args)


def printf(format, *args):
    sys.stdout.write(sprintf(format, *args))


def clearLine():
    sys.stdout.write("\033[K")  # Clear to the end of line


def cursorUpOneLine():
    sys.stdout.write("\033[F")  # Cursor up one line


def cursorUpLines(n):
    while n > 0:
        clearLine()
        cursorUpOneLine()
        clearLine()
        n -= 1
