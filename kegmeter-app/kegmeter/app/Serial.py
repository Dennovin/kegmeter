import logging
import re
import serial
import serial.tools.list_ports_posix
import struct
import time

from kegmeter.common import Config

HEADER_SIZE = 8
MAX_ERRORS_BEFORE_RECONNECT = 10

class SerialListener(object):
    def __init__(self, kegmeter_status):
        self.kegmeter_status = kegmeter_status

        self.hardware_id = Config.get("hardware_id")
        self.statuses = dict()
        self.errors = 0

    def try_connect(self):
        while not (hasattr(self, "port") or self.kegmeter_status.interrupt_event.is_set()):
            try:
                self.connect()
            except IOError:
                time.sleep(5)
            except:
                raise

    def connect(self):
        hwinfo_re = re.compile("^USB.*PID=([0-9a-f\:]+)")
        for dev, dev_name, hwinfo in serial.tools.list_ports_posix.comports():
            match = hwinfo_re.match(hwinfo)
            if match is not None and match.group(1) == self.hardware_id:
                logging.info("Found device on port {}".format(dev))
                self.port = serial.Serial(dev, 38400, timeout=5)

        if not hasattr(self, "port"):
            logging.error("Couldn't find device.")
            raise IOError()

    def reconnect(self):
        logging.warning("Too many errors on serial port - attempting to reconnect")
        self.errors = 0

        try:
            self.port.close()
        except Exception as e:
            logging.warning("Couldn't close port: {}".format(e))

        del self.port
        self.try_connect()

    def receive_packet(self):
        if self.errors > MAX_ERRORS_BEFORE_RECONNECT:
            self.reconnect()

        try:
            self.port.write("1")

            header = bytearray(self.port.read(HEADER_SIZE))

            buffer_size = int(header[0])
            num_taps = int(header[1])
            num_temp = int(header[2])
            num_ports = num_taps + num_temp
        except Exception as e:
            logging.error("Error reading header: {}".format(e))
            self.errors += 1
            return

        try:
            response = self.port.read(buffer_size - HEADER_SIZE)
            self.port.flush()
        except Exception as e:
            logging.error("Error reading from device: {}".format(e))
            return

        if len(response) != 8 * num_ports:
            logging.error("Invalid response length")
            return

        for i in range(num_taps):
            if i + 1 not in self.kegmeter_status.tap_statuses:
                self.kegmeter_status.add_tap(i + 1)

        values = struct.unpack("<" + ("Q" * num_ports), response)

        taps = values[:num_taps]
        temp = values[num_taps:]

        # Tap meters
        for i, val in enumerate(taps):
            if val > 0:
                logging.debug("Output on port {}: {} pulses".format(i, val))
                self.kegmeter_status.update_tap(i + 1, val)

        self.kegmeter_status.cleanup_taps()

        # Temperature monitors
        for i, val in enumerate(temp):
            temp_c = (val * 500.0 / 1023.0) - 50.0
            self.kegmeter_status.update_temp(i + 1, temp_c)

    def listen(self, interval=0.1):
        self.try_connect()

        while not self.kegmeter_status.interrupt_event.is_set():
            self.receive_packet()
            time.sleep(interval)

        logging.error("Serial listener exiting")
