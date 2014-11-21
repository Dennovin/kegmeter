import requests
import urlparse

from kegmeter.common import Config

class DBClient(object):
    @classmethod
    def get_taps(cls):
        host = "{}:{}".format(Config.get("web_remote_host"), Config.get("web_remote_port"))
        url = urlparse.urljoin(host, "json")
        req = requests.get(url)
        return req.json()

