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

feh \
    --hide-pointer \
    --borderless \
    --slideshow-delay 300 \
    -B black \
    --fullscreen \
    --auto-zoom \
    --reload 1800 \
    --recursive \
    --caption-path captions \
    /home/pi/Pictures/slideshow/
