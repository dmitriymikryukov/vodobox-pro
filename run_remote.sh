#!/bin/bash
tar -cvzf ../xdat.tgz .
scp ../xdat.tgz kiosk@10.7.0.3:~/vodobox-pro
ssh kiosk@10.7.0.3 <<EOF
cd ~/vodobox-pro
tar -xzvf ./xdat.tgz
rm ./xdat.tgz
./run.sh
EOF