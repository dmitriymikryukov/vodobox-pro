import sys

def run_gui(IPC):
    from ui import app
    app.sgn_gui = IPC
    from ui.widgets import MainWindow
    window = MainWindow()
    window.showFullScreen()

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui(None))
