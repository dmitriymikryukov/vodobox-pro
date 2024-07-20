#!/bin/bash

./vendor/run.sh

export DISPLAY=:0

ps aux  |  grep -i ./boot.py  |  awk '{print $2}'  |  xargs sudo kill -9
python3 ./boot.py
ps aux  |  grep -i ./boot.py  |  awk '{print $2}'  |  xargs sudo kill -9
ps aux  |  grep -i ./vendor/guiboard.py  |  awk '{print $2}'  |  xargs sudo kill -9
