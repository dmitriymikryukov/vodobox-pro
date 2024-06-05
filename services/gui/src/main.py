from ui.widgets import MainWindow
from ui import app
import sys


window = MainWindow()
window.showFullScreen()

window.show()
sys.exit(app.exec())
