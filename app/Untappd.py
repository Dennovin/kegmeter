import memcache
import requests
import urlparse

from Config import Config


class Untappd(object):
    API_URL = "https://api.untappd.com/v4"

    @classmethod
    def api_request(cls, endpoint, params=None):
        if params is None:
            params = dict()

        params["client_id"] = Config.get("untappd_api_id")
        params["client_secret"] = Config.get("untappd_api_secret")

        url = urlparse.urljoin(cls.API_URL, endpoint)
        req = requests.get(url, params=params)
        return req.json()


class Beer(object):
    memcache = memcache.Client(["127.0.0.1:11211"])

    @classmethod
    def new_from_id(cls, beer_id):
        obj = cls.memcache.get(beer_id.encode("utf-8"))
        if obj:
            return obj

        endpoint = "/v4/beer/info/{}".format(beer_id)
        data = Untappd.api_request(endpoint)
        beer = data["response"]["beer"]

        obj = cls()
        obj.beer_id = beer["bid"]
        obj.beer_name = beer["beer_name"]
        obj.beer_style = beer["beer_style"]
        obj.label = beer["beer_label"]
        obj.description = beer["beer_description"]
        obj.abv = beer["beer_abv"]
        obj.brewery_name = beer["brewery"]["brewery_name"]
        obj.brewery_loc = "{}, {}, {}".format(
            beer["brewery"]["location"]["brewery_city"],
            beer["brewery"]["location"]["brewery_state"],
            beer["brewery"]["country_name"],
            )

        cls.memcache.set(beer_id.encode("utf-8"), obj, 60 * 60 * 24)
        return obj
