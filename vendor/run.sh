#!/bin/bash

export DISPLAY=:0

ps aux  |  grep -i ./vendor/guiboard.py  |  awk '{print $2}'  |  xargs sudo kill -9
sudo python3 ./vendor/guiboard.py &
