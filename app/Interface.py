import gobject
import gtk
import logging
import os
import pango
import pygtk
import requests
import urlparse

from Config import Config
from DB import DB

mysterybeer_file = os.path.join(Config.base_dir(), "images", "mysterybeer.png")

class TapDisplay(gtk.VBox):
    def __init__(self, tap_id):
        super(TapDisplay, self).__init__()

        self.tap_id = tap_id
        self.beer_id = None

        self.image = gtk.Image()
        self.pack_start(self.image, expand=False, padding=40)
        self.image.show()

        self.beer_name = gtk.Label()
        self.beer_name.modify_font(pango.FontDescription("PT Sans Bold 18"))
        self.pack_start(self.beer_name, expand=False)
        self.beer_name.show()

        self.beer_style = gtk.Label()
        self.beer_style.modify_font(pango.FontDescription("PT Sans Bold 16"))
        self.pack_start(self.beer_style, expand=False)
        self.beer_style.show()

        self.brewery_name = gtk.Label()
        self.brewery_name.modify_font(pango.FontDescription("PT Sans 14"))
        self.pack_start(self.brewery_name, expand=False)
        self.brewery_name.show()

        self.brewery_loc = gtk.Label()
        self.brewery_loc.modify_font(pango.FontDescription("PT Sans 14"))
        self.pack_start(self.brewery_loc, expand=False)
        self.brewery_loc.show()

        self.tap_num_box = gtk.EventBox()
        self.tap_num_box.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#eee"))
        self.tap_num = gtk.Label()
        self.tap_num.modify_font(pango.FontDescription("PT Sans Bold 14"))
        self.tap_num_box.add(self.tap_num)
        self.pack_end(self.tap_num_box, expand=False)
        self.tap_num.show()
        self.tap_num_box.show()

        self.bottom_line = gtk.HSeparator()
        self.pack_end(self.bottom_line, expand=False)
        self.bottom_line.show()

        self.abv = gtk.Label()
        self.abv.modify_font(pango.FontDescription("PT Sans Bold 18"))
        self.pack_end(self.abv, expand=False, padding=10)
        self.abv.show()

        self.pct_full_meter = gtk.ProgressBar(adjustment=None)
        self.pct_full_meter.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#ff0"))
        self.pack_end(self.pct_full_meter, expand=False, padding=40)
        self.pct_full_meter.show()

        self.show()

    def update(self, beer):
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
        loader = gtk.gdk.PixbufLoader()

        if "labels" in data:
            img_url = data["labels"]["large"]
            imgreq = requests.get(img_url)
            loader.write(imgreq.content)
        else:
            with open(mysterybeer_file, "r") as img_file:
                loader.write(img_file.read())

        pixbuf = loader.get_pixbuf()
        pixbuf = pixbuf.scale_simple(img_size, img_size, gtk.gdk.INTERP_NEAREST)
        self.image.set_from_pixbuf(pixbuf)
        loader.close()

        self.pct_full_meter.set_fraction(beer["pct_full"])
        self.pct_full_meter.set_text("{}%".format(int(beer["pct_full"] * 100)))


class KegMeter(object):
    def __init__(self, kegmeter_status):
        self.kegmeter_status = kegmeter_status
        self.last_update = None

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.fullscreen()
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#fff"))
        self.window.show()

        self.main_box = gtk.VBox(homogeneous=False)
        self.window.add(self.main_box)

        title_box = gtk.EventBox()
        title_box.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#e8e9de"))

        title = gtk.Label("On Tap")
        title.single_line_mode = True
        title.modify_font(pango.FontDescription("PT Sans Bold 36"))
        title_box.add(title)

        title.show()
        title_box.show()
        self.main_box.pack_start(title_box, expand=False, padding=0)

        self.taps_container = gtk.HBox(homogeneous=False)
        self.taps = dict()

        for i, tap in enumerate(DB.get_taps()):
            tapdisp = TapDisplay(tap["tap_id"])
            tapdisp.kegmeter = self

            if i > 0:
                separator = gtk.VSeparator()
                separator.show()
                self.taps_container.pack_start(separator, expand=False, padding=2)

            self.taps_container.pack_start(tapdisp, expand=True)
            self.taps[tap["tap_id"]] = tapdisp

        self.main_box.pack_start(self.taps_container)
        self.taps_container.show()

        self.main_box.show()

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

        for tap in DB.get_taps():
             self.taps[tap["tap_id"]].update(tap)

    def main(self):
        gobject.idle_add(self.update)
        gtk.main()
