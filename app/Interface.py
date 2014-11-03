import logging
import os
import re
import requests
import urlparse

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

from Config import Config
from DB import DB

mysterybeer_file = os.path.join(Config.base_dir(), "images", "mysterybeer.png")

class TapDisplay(object):
    def __init__(self, tap_id, gtkobj):
        super(TapDisplay, self).__init__()

        self.tap_id = tap_id
        self.gtkobj = gtkobj
        self.beer_id = None
        self.active = False

        for child in self.gtkobj.get_children():
            m = re.match("^(.*)_\d$", Gtk.Buildable.get_name(child))
            if m:
                setattr(self, m.group(1), child)

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

        img_size = int(self.gtkobj.get_allocation().width * 0.9)
        logging.debug("allocation: {}".format(self.gtkobj.get_allocation().width))
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

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(Config.base_dir(), "app", "interface.xml"))
        self.window = self.builder.get_object("OnTap")

        self.style_provider = Gtk.CssProvider()
        self.style_provider.load_from_path(os.path.join(Config.base_dir(), "app", "interface.css"))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.taps = dict()
        for tap in DB.get_taps():
            gtkobj = self.builder.get_object("TapDisplay_{}".format(tap["tap_id"]))
            self.taps[tap["tap_id"]] = TapDisplay(tap["tap_id"], gtkobj)

        self.window.fullscreen()
        self.window.show_all()

    def update(self):
        if self.kegmeter_status.interrupt_event.is_set():
            logging.error("Interface exiting")
            return False

        if not self.kegmeter_status.tap_update_event.is_set():
            return True

        self.kegmeter_status.tap_update_event.clear()

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

