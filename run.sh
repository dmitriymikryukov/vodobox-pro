#!/bin/bash

export DISPLAY=:0

ps aux  |  grep -i ./boot.py  |  awk '{print $2}'  |  xargs sudo kill -9
ps aux  |  grep -i ./vendor/guiboard.py  |  awk '{print $2}'  |  xargs sudo kill -9
sudo python3 ./vendor/guiboard.py &
python3 ./boot.py
ps aux  |  grep -i ./boot.py  |  awk '{print $2}'  |  xargs sudo kill -9
ps aux  |  grep -i ./vendor/guiboard.py  |  awk '{print $2}'  |  xargs sudo kill -9
