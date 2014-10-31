import logging
import os
import requests
import urlparse

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

from Config import Config
from DB import DB

mysterybeer_file = os.path.join(Config.base_dir(), "images", "mysterybeer.png")

class TapDisplay(Gtk.VBox):
    def __init__(self, tap_id):
        super(TapDisplay, self).__init__()

        self.tap_id = tap_id
        self.beer_id = None
        self.active = False

        self.set_name("tap{}".format(self.tap_id))
        self.get_style_context().add_class("tap_display")

        self.parts = [
            { "name": "image", "type": Gtk.Image, "pack": "start" },
            { "name": "beer_name", "type": Gtk.Label, "pack": "start" },
            { "name": "beer_style", "type": Gtk.Label, "pack": "start" },
            { "name": "brewery_name", "type": Gtk.Label, "pack": "start" },
            { "name": "brewery_loc", "type": Gtk.Label, "pack": "start" },
            { "name": "tap_num", "type": Gtk.Label, "pack": "end" },
            { "name": "pct_full_meter", "type": Gtk.ProgressBar, "pack": "end" },
            { "name": "abv", "type": Gtk.Label, "pack": "end" },
            ]

        for part in self.parts:
            gtkobj = part["type"]()
            gtkobj.get_style_context().add_class(part["name"])

            if part["pack"] == "start":
                self.pack_start(gtkobj, False, False, 0)
            else:
                self.pack_end(gtkobj, False, False, 0)

            setattr(self, part["name"], gtkobj)

    def update(self, beer):
        self.make_inactive()

        if beer["beer_id"] == self.beer_id:
            return

        url = urlparse.urljoin(Config.get("brewerydb_url"), "beer/{}?withBreweries=Y&key={}".format(beer["beer_id"], Config.get("brewerydb_api_key")))
        req = requests.get(url, timeout=1)

        try:
            json = req.json()
        except Exception as e:
            logging.error("Couldn't parse JSON from {}: {}".format(url, e))
            return

        self.beer_id = beer["beer_id"]

        data = json["data"]
        loc = data["breweries"][0]["locations"][0]

        self.beer_name.set_text(data["name"])
        self.beer_style.set_text(data["style"]["name"])
        self.brewery_name.set_text(data["breweries"][0]["name"])
        self.brewery_loc.set_text(loc["locality"] + ", " + loc["region"] + ", " + loc["country"]["isoThree"])
        self.abv.set_text("{}%".format(data["abv"]))

        img_size = int(self.get_allocation().width * 0.9)
        logging.debug("allocation: {}".format(self.get_allocation().width))
        loader = GdkPixbuf.PixbufLoader()

        if "labels" in data:
            img_url = data["labels"]["large"]
            imgreq = requests.get(img_url)
            loader.write(imgreq.content)
        else:
            with open(mysterybeer_file, "r") as img_file:
                loader.write(img_file.read())

        pixbuf = loader.get_pixbuf()
        pixbuf = pixbuf.scale_simple(img_size, img_size, GdkPixbuf.InterpType.BILINEAR)
        self.image.set_from_pixbuf(pixbuf)
        loader.close()

        self.pct_full_meter.set_fraction(beer["pct_full"])
        self.pct_full_meter.set_text("{}%".format(int(beer["pct_full"] * 100)))

    def make_active(self):
        if self.active:
            return

        self.get_style_context().add_class("active")

    def make_inactive(self):
        if not self.active:
            return

        self.get_style_context().remove_class("active")

class KegMeter(object):
    def __init__(self, kegmeter_status):
        self.kegmeter_status = kegmeter_status
        self.last_update = None

        self.window = Gtk.Window()
        self.window.set_name("OnTap")
        self.window.fullscreen()
        self.window.show_now()

        self.style_provider = Gtk.CssProvider()
        self.style_provider.load_from_path(os.path.join(Config.base_dir(), "app", "interface.css"))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.main_box = Gtk.VBox(homogeneous=False)
        self.window.add(self.main_box)

        title_box = Gtk.EventBox()

        title = Gtk.Label("On Tap")
        title_box.add(title)
        title.get_style_context().add_class("title")

        self.main_box.pack_start(title_box, False, False, 10)

        self.taps_container = Gtk.HBox(homogeneous=True)
        self.taps = dict()

        for i, tap in enumerate(DB.get_taps()):
            tapdisp = TapDisplay(tap["tap_id"])
            tapdisp.kegmeter = self

            self.taps_container.pack_start(tapdisp, True, True, 0)
            self.taps[tap["tap_id"]] = tapdisp

        self.main_box.add(self.taps_container)

        self.window.show_all()

    def update(self):
        if self.kegmeter_status.interrupt_event.is_set():
            logging.error("Interface exiting")
            return False

        if not self.kegmeter_status.tap_update_event.is_set():
            return True

        self.kegmeter_status.tap_update_event.clear()
        for i, tap in self.taps.items():
            alloc = tap.get_allocation()
            if alloc.x < 0:
                return True

        active_tap = self.kegmeter_status.get_active_tap()
        if active_tap is not None:
            self.taps[active_tap.tap_id].make_active()
            return True

        for tap in DB.get_taps():
             self.taps[tap["tap_id"]].update(tap)

        return True

    def main(self):
        Gdk.threads_init()

        GObject.idle_add(self.update)
        Gtk.main()

