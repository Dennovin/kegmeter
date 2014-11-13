#!/bin/bash

# Download minimal Raspbian image, write to card, and resize partition

CARD_DEV=$1

wget https://dl.dropbox.com/u/45842273/2012-07-15-wheezy-raspian-minimal.img.7z
7z x 2012-07-15-wheezy-raspian-minimal.img.7z
sudo dd bs=4M if=2012-07-15-wheezy-raspian-minimal.img of=${CARD_DEV}

START=$( sudo parted ${CARD_DEV} print | grep "^ 2" | awk -e '{print $2}' )
sudo parted ${CARD_DEV} rm 2
sudo parted ${CARD_DEV} mkpart primary ext4 ${START} 100%
sudo e2fsck -f ${CARD_DEV}2
sudo resize2fs ${CARD_DEV}2

