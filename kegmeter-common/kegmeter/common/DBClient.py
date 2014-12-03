import logging
import requests
import urlparse

from kegmeter.common import Config

class DBClient(object):
    last_tap_data = []

    @classmethod
    def web_host(cls):
        return "{}:{}".format(Config.get("web_remote_host"), Config.get("web_remote_port"))

    @classmethod
    def get_taps(cls):
        url = urlparse.urljoin(cls.web_host(), "json")
        try:
            req = requests.get(url)
            cls.last_tap_data = req.json()
        except requests.exceptions.ConnectionError as e:
            logging.error("Couldn't update tap info: {}".format(e))

        return cls.last_tap_data

    @classmethod
    def update_amount_poured(cls, tap_id, pulses):
        logging.debug("Sending update for tap {}, {} pulses".format(tap_id, pulses))

        url = urlparse.urljoin(cls.web_host(), "update")
        try:
            requests.post(url, params={
                    "update_secret": Config.get("update_secret"),
                    "tap_id": tap_id,
                    "pulses": pulses,
                    })
        except requests.exceptions.ConnectionError as e:
            logging.error("Couldn't update amount poured ({} on tap {}): {}".format(pulses, tap_id, e))

    @classmethod
    def update_temperature(cls, sensor_id, deg_c):
        logging.debug("Sending update for temperature sensor {}, {} degrees".format(sensor_id, deg_c))

        url = urlparse.urljoin(cls.web_host(), "update")
        try:
            requests.post(url, params={
                    "update_secret": Config.get("update_secret"),
                    "sensor_id": sensor_id,
                    "deg_c": deg_c,
                    })

        except requests.exceptions.ConnectionError as e:
            logging.error("Couldn't update temperature: {}".format(e))
