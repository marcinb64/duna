#!/bin/bash

export DISPLAY=:0

echo "Waiting for X server..."
while ( ! xset q >/dev/null 2>&1); do
    sleep 1;
done
echo "ok"

xset s noblank
xset s off
xset -dpms

INSTALL_DIR=$(dirname $0)
python3 ${INSTALL_DIR}/app.py --config=${HOME}/duna.json
