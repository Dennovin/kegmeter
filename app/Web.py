import logging
import memcache
import oauth2client.client
import os
import simplejson
import tornado.auth
import tornado.template
import tornado.web

from Config import Config
from DB import DB

template_dir = os.path.join(Config.base_dir(), "web", "templates")
static_dir = os.path.join(Config.base_dir(), "web", "static")


class StaticHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.loader = tornado.template.Loader(template_dir)


class IndexHandler(StaticHandler):
    def get(self):
        self.write(self.loader.load("index.html").generate())


class JsonHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.loader = tornado.template.Loader(template_dir)

    def get(self):
        self.write(simplejson.dumps(DB.get_taps()))


class ApiHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.memcache = memcache.Client(["127.0.0.1:11211"])
        self.http = tornado.httpclient.AsyncHTTPClient()

    @tornado.web.asynchronous
    def get(self, url_part):
        self.url = Config.get("brewerydb_url") + self.request.uri.replace("/brewerydb", "")
        self.url = tornado.httputil.url_concat(self.url, {"key": Config.get("brewerydb_api_key")})

        response = self.memcache.get(self.url)
        if response is None:
            self.http.fetch(self.url, self.print_response)
        else:
            self.write(response)
            self.finish()

    def print_response(self, response):
        self.memcache.set(self.url, response.body, 60 * 60 * 24)
        self.write(response.body)
        self.finish()


class AuthHandler(tornado.web.RequestHandler, tornado.auth.GoogleOAuth2Mixin):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument("code", False):
            user = yield self.get_authenticated_user(
                redirect_uri=Config.get("google_oauth_url"),
                code=self.get_argument("code"),
                )

            jwt = oauth2client.client.verify_id_token(user["id_token"], Config.get("google_oauth_key"))

            if jwt and jwt["email"] and jwt["email"].endswith("@omniti.com"):
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

        if not user:
            self.redirect("/auth")
            return

        if action == "update":
            db = DB.connect()

            tap_id = self.get_argument("tap_id");
            beer_id = self.get_argument("beer_id");

            cursor = self.db.cursor()
            cursor.execute("update taps set beer_id = ?, last_updated = strftime('%s', 'now'), last_updated_by = ? where tap_id = ?", [beer_id, user, tap_id])
            cursor.close()

            self.db.commit()

            self.write(simplejson.dumps({"tap_id": tap_id, "beer_id": beer_id}))


class AdminIndexHandler(StaticHandler):
    def get(self):
        if not self.get_secure_cookie("email"):
            self.redirect("/auth")
            return

        self.write(self.loader.load("admin.html").generate(taps=DB.get_taps()))


class WebServer(object):
    def __init__(self, kegmeter_status):
        self.kegmeter_status = kegmeter_status

    def listen(self):
        self.app = tornado.web.Application(
            [
                (r"/", IndexHandler),
                (r"/(favicon.ico)", tornado.web.StaticFileHandler, {"path": static_dir}),
                (r"/json", JsonHandler),
                (r"/brewerydb/(.*)", ApiHandler),
                (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": static_dir}),
                (r"/auth", AuthHandler),
                (r"/admin/(.*)", AdminHandler),
                (r"/admin", AdminIndexHandler),
                ],
            cookie_secret=Config.get("cookie_secret"),
            google_oauth={
                "secret": Config.get("google_oauth_secret"),
                },
            )

        self.app.listen(Config.get("web_port"))
        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.ioloop.start()

    def shutdown(self):
        logging.error("Web server exiting")
        self.ioloop.stop()

