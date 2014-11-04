import logging
import os
import re
import requests

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

from Config import Config
from DB import DB
from Untappd import Beer

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

    def update(self, tap):
        self.make_inactive()

        if tap["beer_id"] == self.beer_id:
            return

        try:
            beer = Beer.new_from_id(tap["beer_id"])
        except Exception as e:
            logging.error("Couldn't look up beer ID {}: {}".format(beer_id, e))
            return

        self.beer_name.set_text(beer.beer_name)
        self.beer_style.set_text(beer.beer_style)
        self.brewery_name.set_text(beer.brewery_name)
        self.brewery_loc.set_text(beer.brewery_loc)
        self.abv.set_text("{}%".format(beer.abv))

        img_size = int(self.gtkobj.get_allocation().width * 0.9)
        logging.debug("allocation: {}".format(self.gtkobj.get_allocation().width))
        loader = GdkPixbuf.PixbufLoader()

        img_url = beer.label
        imgreq = requests.get(img_url)
        loader.write(imgreq.content)

        pixbuf = loader.get_pixbuf()
        pixbuf = pixbuf.scale_simple(img_size, img_size, GdkPixbuf.InterpType.BILINEAR)
        self.image.set_from_pixbuf(pixbuf)
        loader.close()

        self.pct_full_meter.set_fraction(tap["pct_full"])
        self.pct_full_meter.set_text("{}%".format(int(tap["pct_full"] * 100)))

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
        self.builder.add_from_file(os.path.join(Config.base_dir(), "app", "interface.glade"))
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
            self.shutdown()
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

    def shutdown(self):
        logging.error("Interface exiting")
        self.window.destroy()
        Gtk.main_quit()
