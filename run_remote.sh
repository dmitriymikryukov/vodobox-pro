#!/bin/bash
./git_push.sh
ssh <<EOF
cd /opt/kiosk/vodobox-pro
./git_pull.sh
./run.sh
EOF