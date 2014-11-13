kegmeter
========

Installation

`pi/download.sh <DEVICE>` will download a minimal Raspbian image, write it to `<DEVICE>`, and resize the partition.
Once your system is running, you can log in with username `pi` and password `raspberry`, and download and run `setup.sh`:

    wget https://raw.githubusercontent.com/Dennovin/kegmeter/master/pi/setup.sh
    chmod +x setup.sh
    ./setup.sh

You'll need to create the `config/settings.json` file. An example is provided.
