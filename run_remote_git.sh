#!/bin/bash
./git_pull.sh
./git_push.sh
ssh kiosk@10.7.0.3 <<EOF
cd /opt/kiosk/vodobox-pro
sudo ./git_pull.sh
./run.sh
EOF