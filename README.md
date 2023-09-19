# Duna

## About

An application for downloading and displaying the latest images from NASA Mars rovers.

I developed this to run on a Raspberry Pi connected to a wall-mounted monitor.
Every day it checks for new raw images, filters out some low-res engineering and test images,
and runs a continuous slide show.

The slide show can also include statically pre-configured web pages and images.

## Installation instructions for Raspberry Pi

1. Get a free NASA API key from https://api.nasa.gov

2. Install Raspberry Pi OS (desktop version)
   - configure your user name, hostname, network access, and screen resolution
   - use raspi-config to disable screen blanking

3. Install dependencies

    `sudo apt install python3-wget`

4. Download this repository into `/opt/duna` (you should have `/opt/duna/bin` and `/opt/duna/share` dirs)
    ```
    cd /opt
    sudo git clone https://github.com/marcinb64/duna
    sudo chown -R <username> duna
    ```

5. Prepare directory for the images
    ```
    sudo mkdir /var/lib/duna
    sudo chown <username> /var/lib/duna
    ```

6. Copy the configuration file (`share/duna.json`) to your home dir
    ```
    cp /opt/duna/share/duna.json ~/
    ```

7. Edit `duna.json` and enter your API KEY. Customize any other options as needed.

8. Install and start the service
    ```
    sudo ln -s /opt/duna/share/systemd/duna.service /etc/systemd/system/
    sudo systemctl enable duna
    sudo systemctl start duna
    ```

9. Run "crontab -e" to schedule a job for cleaning up old images
    ```
    # m h  dom mon dow   command
    5 0 * * * /opt/duna/bin/limit_disk_usage.sh /var/lib/duna/rovers
    ```

10. Optionally, schedule cron jobs for turning the display off for the night
    ```
    # turn off at midnight
    0 0 * * * DISPLAY=:0 xrandr --output HDMI-1 --off
    # turn on at 7am
    0 7 * * * DISPLAY=:0 xrandr --output HDMI-1 --auto
    ```

## Customization

The file `~/duna.json` configures the download and sliedshow.
- `interval` - the time to display one image
- `updateInterval` - the time between checking for new images
- `firstUpdateDelay` - the time to wait after starting the app, before checking for new images
- `APOD` entry in the `updates` section downloads the latest Astronomy Picture Of the Day, and saves it under `/var/lib/duna/slideshow/nasa-apod.jpg`
- `urls` in `static` section lists images and web pages to show in between the rover images

The app creates 3 "channels" of slideshows, one for Curiosity rover, one for Perseverance, and one for the static images/URLs.
In order to give each channel to be displayed regularly, it limits the number of images displayed from one rover (`sequenceLimit` setting in the config file).
The last position in each channel is remembered, so eventually it should cycle through all of them.
