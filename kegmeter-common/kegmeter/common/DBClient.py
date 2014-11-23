import logging
import requests
import urlparse

from kegmeter.common import Config

class DBClient(object):
    @classmethod
    def web_host(cls):
        return "{}:{}".format(Config.get("web_remote_host"), Config.get("web_remote_port"))

    @classmethod
    def get_taps(cls):
        url = urlparse.urljoin(cls.web_host(), "json")
        req = requests.get(url)
        return req.json()

    @classmethod
    def update_amount_poured(cls, tap_id, pulses):
        logging.debug("Sending update for tap {}, {} pulses".format(tap_id, pulses))

        url = urlparse.urljoin(cls.web_host(), "update")
        requests.post(url, params={
                "update_secret": Config.get("update_secret"),
                "tap_id": tap_id,
                "pulses": pulses,
                })
