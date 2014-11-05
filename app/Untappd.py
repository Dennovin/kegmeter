import ago
from datetime import datetime
import memcache
import requests
import simplejson
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

    def to_dict(self):
        return {
            "beer_id": self.beer_id,
            "beer_name": self.beer_name,
            "beer_style": self.beer_style,
            "label": self.label,
            "description": self.description,
            "abv": self.abv,
            "brewery_name": self.brewery_name,
            "brewery_loc": self.brewery_loc,
            }

    def to_json(self):
        return simplejson.dumps(self.to_dict())

    @classmethod
    def new_from_api_response(cls, beer, brewery=None):
        if brewery is None and "brewery" in beer:
            brewery = beer["brewery"]

        obj = cls()
        obj.beer_id = beer["bid"]
        obj.beer_name = beer["beer_name"]
        obj.beer_style = beer["beer_style"]
        obj.label = beer["beer_label"]
        obj.description = beer["beer_description"]
        obj.abv = beer["beer_abv"]
        obj.brewery_name = brewery["brewery_name"]
        obj.brewery_loc = "{}, {}, {}".format(
            brewery["location"]["brewery_city"],
            brewery["location"]["brewery_state"],
            brewery["country_name"],
            )

        return obj

    @classmethod
    def new_from_id(cls, beer_id):
        endpoint = "/v4/beer/info/{}".format(beer_id)

        data = cls.memcache.get(str(beer_id))
        if data is None:
            data = Untappd.api_request(endpoint)
            cls.memcache.set(str(beer_id), data, 60 * 60 * 24)

        beer = data["response"]["beer"]

        obj = cls.new_from_api_response(beer)
        return obj

    @classmethod
    def search(cls, search_string):
        endpoint = "/v4/search/beer"
        data = Untappd.api_request(endpoint, {"q": search_string})
        beers = []

        for item in data["response"]["beers"]["items"]:
            beers.append(cls.new_from_api_response(beer=item["beer"], brewery=item["brewery"]))

        return beers


class Checkin(object):
    @property
    def beer(self):
        if not hasattr(self, "_beer"):
            self._beer = Beer.new_from_id(self.beer_id)

        return self._beer

    @property
    def time_since(self):
        try:
            delta = datetime.now() - datetime.strptime(self.created_at, "%a, %d %b %Y %H:%M:%S +0000")
            return ago.human(delta, precision=2)
        except AttributeError as e:
            return ""
        except:
            raise

    @classmethod
    def new_from_api_response(cls, response):
        obj = cls()

        obj.checkin_id = response["checkin_id"]
        obj.user_name = response["user"]["first_name"]
        obj.user_avatar = response["user"]["user_avatar"]
        obj.created_at = response["created_at"]
        obj.comment = response["checkin_comment"]
        obj.beer_id = response["beer"]["bid"]

        return obj

    @classmethod
    def get_latest(cls):
        endpoint = "/v4/venue/checkins/{}".format(Config.get("untappd_venue_id"))
        data = Untappd.api_request(endpoint)

        checkins = []
        for item in data["response"]["checkins"]["items"]:
            checkins.append(cls.new_from_api_response(item))

        return checkins
