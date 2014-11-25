import logging
import threading
import time

from kegmeter.common import DBClient

class TapStatus(object):
    def __init__(self, tap_id):
        self.tap_id = tap_id
        self.pulses = 0
        self.clear()

    def update(self, pulses):
        self.pulses += pulses
        self.last_update = time.time()

    def is_active(self):
        return (self.last_update is not None)

    def is_done(self):
        return (self.last_update is not None and self.last_update < time.time() - 5)

    def clear(self):
        if self.pulses > 0:
            DBClient.update_amount_poured(self.tap_id, self.pulses)

        self.pulses = 0
        self.last_update = None


class KegmeterStatus(object):
    def __init__(self):
        self.tap_update_event = threading.Event()
        self.interrupt_event = threading.Event()

        self.tap_statuses = dict()
        self.temp_sensors = dict()

        self.last_temp_update = dict()

    def interrupt(self, signal, frame):
        logging.error("Got keyboard interrupt, exiting")
        self.tap_update_event.set()
        self.interrupt_event.set()

    def add_tap(self, tap_id):
        self.tap_statuses[tap_id] = TapStatus(tap_id)

    def update_tap(self, tap_id, pulses):
        self.tap_update_event.set()
        self.tap_statuses[tap_id].update(pulses)

    def cleanup_taps(self):
        for tap in self.tap_statuses.values():
            if tap.is_done():
                tap.clear()
                self.tap_update_event.set()

    def update_temp(self, sensor_id, deg_c):
        self.temp_sensors[sensor_id] = (0.95 * self.temp_sensors.get(sensor_id, deg_c)) + (0.05 * deg_c)

        if time.time() - 60 > self.last_temp_update.get(sensor_id):
            DBClient.update_temperature(sensor_id, self.temp_sensors[sensor_id])
            self.last_temp_update[sensor_id] = time.time()
