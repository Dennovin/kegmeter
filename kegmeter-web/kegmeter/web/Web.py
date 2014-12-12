import httplib
import logging
import oauth2client.client
import os
import pkg_resources
import simplejson
import tornado.auth
import tornado.template
import tornado.web

from kegmeter.common import Config, Beer
from kegmeter.web import DB

template_dir = pkg_resources.resource_filename(__name__, "templates")
static_dir = pkg_resources.resource_filename(__name__, "static")


class StaticHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.loader = tornado.template.Loader(template_dir)


class IndexHandler(StaticHandler):
    def get(self):
        self.write(self.loader.load("index.html").generate(taps=DB.get_taps()))


class JsonHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(simplejson.dumps(DB.get_taps()))


class StatsHandler(tornado.web.RequestHandler):
    def get(self):
        status = {
            "temperatures": DB.get_temps(),
            "taps": DB.get_taps(),
            }

        self.write(simplejson.dumps(status))


class APIBeerDetails(tornado.web.RequestHandler):
    def get(self, beer_id):
        beer = Beer.new_from_id(beer_id)
        self.write(beer.to_json())


class APISearch(tornado.web.RequestHandler):
    def get(self):
        results = Beer.search(self.get_argument("q"))
        self.write(simplejson.dumps([i.to_dict() for i in results]))


class UpdateHandler(tornado.web.RequestHandler):
    def post(self):
        if self.get_argument("update_secret") != Config.get("update_secret"):
            raise tornado.web.HTTPError(httplib.UNAUTHORIZED)

        if self.get_argument("tap_id", False) and self.get_argument("pulses", False):
            DB.update_amount_poured(self.get_argument("tap_id"), self.get_argument("pulses"))

        if self.get_argument("sensor_id", False) and self.get_argument("deg_c", False):
            DB.update_temperature(self.get_argument("sensor_id"), self.get_argument("deg_c"))


class AuthHandler(tornado.web.RequestHandler, tornado.auth.GoogleOAuth2Mixin):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument("code", False):
            user = yield self.get_authenticated_user(
                redirect_uri=Config.get("google_oauth_url"),
                code=self.get_argument("code"),
                )

            jwt = oauth2client.client.verify_id_token(user["id_token"], Config.get("google_oauth_key"))

            if jwt and jwt["email"] and jwt["email"].endswith("@" + Config.get("admin_email_domain")):
                self.set_secure_cookie("email", jwt["email"])
                self.redirect("/admin")
            else:
                self.set_status(403)
                self.finish()

        else:
            yield self.authorize_redirect(
                redirect_uri=Config.get("google_oauth_url"),
                client_id=Config.get("google_oauth_key"),
                scope=["email", "profile"],
                response_type="code",
                extra_params={"approval_prompt": "auto"},
                )


class AdminHandler(tornado.web.RequestHandler):
    def post(self, action):
        user = self.get_secure_cookie("email")

        if not user and not Config.get("debug_admin"):
            self.redirect("/auth")
            return

        if action == "update":
            db = DB.connect()

            tap_id = self.get_argument("tap_id");
            beer_id = self.get_argument("beer_id");

            cursor = db.cursor()
            cursor.execute("update taps set beer_id = ?, last_updated = strftime('%s', 'now'), last_updated_by = ?, amount_poured = 0 where tap_id = ?", [beer_id, user, tap_id])
            cursor.close()

            db.commit()

            self.write(simplejson.dumps({"tap_id": tap_id, "beer_id": beer_id}))


class AdminIndexHandler(StaticHandler):
    def get(self):
        if not self.get_secure_cookie("email") and not Config.get("debug_admin"):
            self.redirect("/auth")
            return

        self.write(self.loader.load("admin.html").generate(taps=DB.get_taps()))


class WebServer(object):
    def listen(self):
        self.app = tornado.web.Application(
            [
                (r"/", IndexHandler),
                (r"/(favicon.ico)", tornado.web.StaticFileHandler, {"path": static_dir}),
                (r"/json", JsonHandler),
                (r"/stats", StatsHandler),
                (r"/api/beer/(.*)", APIBeerDetails),
                (r"/api/search", APISearch),
                (r"/update", UpdateHandler),
                (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": static_dir}),
                (r"/auth", AuthHandler),
                (r"/admin/(.*)", AdminHandler),
                (r"/admin", AdminIndexHandler),
                ],
            cookie_secret=Config.get("cookie_secret"),
            google_oauth={
                "url": Config.get("google_oauth_url"),
                "key": Config.get("google_oauth_key"),
                "secret": Config.get("google_oauth_secret"),
                },
            )

        self.app.listen(Config.get("web_port"))
        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.ioloop.start()

    def shutdown(self):
        logging.error("Web server exiting")
        self.ioloop.stop()

