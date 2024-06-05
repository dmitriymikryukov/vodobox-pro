from ui.widgets import MainWindow
from ui import app
import sys

def run_gui(IPC):
    window = MainWindow()
    window.showFullScreen()

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_gui(None)
