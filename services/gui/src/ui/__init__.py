from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase
from dotenv import load_dotenv
import logging
import sys
import os

os.environ["XDG_SESSION_TYPE"] = "xcb"
load_dotenv()
logging.basicConfig(
    level=logging.INFO
)

app = QApplication(sys.argv)
app.setStyle('Fusion')

family_font_id = QFontDatabase.addApplicationFont(
    os.path.join(os.getcwd(), '..', 'resources', 'fonts', 'Rubik', 'static', 'Rubik-Regular.ttf'))

if family_font_id < 0:
    logging.error('Error on loading fonts to app')

