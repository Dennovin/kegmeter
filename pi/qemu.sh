#!/bin/bash

# Download minimal Raspbian image, resize partition, and start up with qemu

wget https://dl.dropbox.com/u/45842273/2012-07-15-wheezy-raspian-minimal.img.7z
7z x 2012-07-15-wheezy-raspian-minimal.img.7z
qemu-img resize 2012-07-15-wheezy-raspian-minimal.img 4GB

START=$( parted 2012-07-15-wheezy-raspian-minimal.img print | grep "^ 2" | awk -e '{print $2}' )
END=$( parted 2012-07-15-wheezy-raspian-minimal.img print | grep "^Disk" | cut -d':' -f2 )
parted 2012-07-15-wheezy-raspian-minimal.img rm 2
parted -s 2012-07-15-wheezy-raspian-minimal.img mkpart primary ext4 $START $END

START_BYTE=$( echo "$( fdisk -l 2012-07-15-wheezy-raspian-minimal.img | grep img2 | awk -e '{print $2}' ) * 512" | bc )
DEV=$( sudo losetup -f --show 2012-07-15-wheezy-raspian-minimal.img -o $START_BYTE )

sudo e2fsck -f $DEV -y
sudo resize2fs $DEV

sudo losetup -d $DEV

qemu-system-arm -kernel kernel-qemu -cpu arm1176 -m 256 -M versatilepb -no-reboot -serial stdio -append "root=/dev/sda2 panic=1" -hda 2012-07-15-wheezy-raspian-minimal.img

