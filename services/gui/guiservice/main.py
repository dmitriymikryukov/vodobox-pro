from ui.widgets import MainWindow
from ui import app
import sys


def run_gui(IPC):
    app.sgn_gui = IPC
    window = MainWindow()
    window.showFullScreen()

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui(None))
