from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase
import sys
import os

os.environ["XDG_SESSION_TYPE"] = "xcb"

app = QApplication(sys.argv)
app.setStyle('Fusion')

family_font_id = QFontDatabase.addApplicationFont(
    os.path.join(os.getcwd(), '..', 'resources', 'fonts', 'Rubik', 'static', 'Rubik-Regular.ttf'))

if family_font_id < 0:
    app.sgn_gui.error('Error on loading fonts to app')

