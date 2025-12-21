import sys
from . import cli
from . import gui

def main():
    if len(sys.argv) > 1:
        cli.main()
    else:
        gui.main()

if __name__ == "__main__":
    main()
