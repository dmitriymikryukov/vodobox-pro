# Vodobox GUI

### команда для создания ts-файлов
- pylupdate5 -noobsolete src/translation/translation_sources.txt 

### команда для генерации py файла из ui
pyuic5 -x services/gui/resources/ui_interface/waiting_window.ui -o services/gui/guiservice/ui/converted/gen_waiting_window.py