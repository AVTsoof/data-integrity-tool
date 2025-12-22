import sys
from . import cli
from . import gui
from .core import ensure_7z_installed, DependencyError
import tkinter.messagebox

def main():
    try:
        ensure_7z_installed()
        if len(sys.argv) > 1:
            cli.main()
        else:
            gui.main()
    except DependencyError as e:
        if len(sys.argv) > 1:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        else:
            # If GUI mode, we need to create a root window to show the error
            # because gui.main() hasn't been called yet.
            from .gui import DataIntegrityApp
            app = DataIntegrityApp()
            app.withdraw() # Hide the main window
            tkinter.messagebox.showerror("Dependency Error", str(e))
            app.destroy()
            sys.exit(1)

if __name__ == "__main__":
    main()
