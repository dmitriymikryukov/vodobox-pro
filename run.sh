#!/bin/bash

export display=:0

ps aux  |  grep -i ./boot.py  |  awk '{print $2}'  |  xargs sudo kill -9
python3 ./boot.py
ps aux  |  grep -i ./boot.py  |  awk '{print $2}'  |  xargs sudo kill -9
