#!/bin/bash

# Starting from a minimal install of Raspbian
# from https://dl.dropbox.com/u/45842273/2012-07-15-wheezy-raspian-minimal.img.7z

# Update packages and fix locale
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update
sudo apt-get -y install locales
sudo apt-get -y upgrade -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"

# Install required packages
sudo apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" install \
  git lxde python python-dev python-pip python-tk python-imaging-tk libsqlite3-dev \
  libjpeg-dev tk8.6-dev tcl8.6-dev memcached x11-xserver-utils unclutter

# Create kegmeter user and download application
sudo useradd -m -s /bin/bash kegmeter

sudo mkdir -p /opt/kegmeter/etc /opt/kegmeter/log
sudo chown -R kegmeter /opt/kegmeter

sudo pip install kegmeter-app

# Add udev rules
sudo tee /etc/udev/rules.d/49-teensy.rules <<EOF
ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789]?", ENV{ID_MM_DEVICE_IGNORE}="1"
ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789]?", ENV{MTP_NO_PROBE}="1"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789]?", MODE:="0666"
KERNEL=="ttyACM*", ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789]?", MODE:="0666"
EOF

# Set up autologin/autostart
sudo update-rc.d lightdm defaults
sudo update-rc.d lightdm enable

sudo tee /etc/lightdm/lightdm.conf <<EOF
[LightDM]

[SeatDefaults]
autologin-user=kegmeter
autologin-user-timeout=0
xserver-allow-tcp=false
session-wrapper=/etc/X11/Xsession

[XDMCPServer]

[VNCServer]

EOF

sudo -u kegmeter mkdir -p /home/kegmeter/.config/autostart
sudo -u kegmeter tee /home/kegmeter/.config/autostart/kegmeter.desktop <<EOF
[Desktop Entry]
Type=Application
Exec=/usr/local/bin/kegmeter_app.py --logfile /opt/kegmeter/log/kegmeter.log
EOF

# Run unclutter to hide mouse cursor
sudo -u kegmeter tee /home/kegmeter/.config/autostart/unclutter.desktop <<EOF
[Desktop Entry]
Type=Application
Exec=/usr/bin/unclutter -idle 0
EOF

# Disable overscan
sudo sed -i -e 's/\#disable_overscan/disable_overscan/g;' /boot/config.txt

# Disable screensaver and powersaving
grep -v "^@xscreensaver" /etc/xdg/lxsession/LXDE/autostart | sudo tee /etc/xdg/lxsession/LXDE/autostart

sudo -u kegmeter tee /home/kegmeter/.xsession <<EOF
xset s off
xset -dpms
xset s noblank

exec /etc/alternatives/x-session-manager
EOF

# Download PT Sans font
wget https://www.google.com/fonts/download?kit=-tlFHQ-l0RbFTifjjgYkyKCWcynf_cDxXwCLxiixG1c -O /tmp/fonts.zip
sudo -u kegmeter mkdir -p /home/kegmeter/.fonts
sudo -u kegmeter unzip /tmp/fonts.zip -d /home/kegmeter/.fonts

# Reboot... and hopefully everything works
sudo reboot
