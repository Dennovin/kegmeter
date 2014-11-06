import logging
import os
import re
import requests

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

from Config import Config
from DB import DB
from Untappd import Beer, Checkin

mysterybeer_file = os.path.join(Config.base_dir(), "images", "mysterybeer.png")


class ObjectContainer(object):
    def find_children(self, gtkobj=None):
        if gtkobj is None:
            gtkobj = self.gtkobj

        for child in gtkobj.get_children():
            m = re.match("^(.*)_\d$", Gtk.Buildable.get_name(child))
            if m:
                setattr(self, m.group(1).lower(), child)

            try:
                self.find_children(child)
            except AttributeError:
                pass

    def load_image(self, image, url):
        try:
            alloc = image.get_allocation()
            imgreq = requests.get(url)
            loader = GdkPixbuf.PixbufLoader.new_with_mime_type(imgreq.headers["content-type"])
            logging.debug(imgreq)
            loader.write(imgreq.content)
            pixbuf = loader.get_pixbuf()
            pixbuf = pixbuf.scale_simple(alloc.width, alloc.height, GdkPixbuf.InterpType.BILINEAR)
            image.set_from_pixbuf(pixbuf)
        except Exception as e:
            logging.error(e)
        finally:
            loader.close()


class TapDisplay(ObjectContainer):
    def __init__(self, tap_id, gtkobj):
        super(TapDisplay, self).__init__()

        self.tap_id = tap_id
        self.gtkobj = gtkobj
        self.beer = None
        self.beer_id = None
        self.amount_poured = None
        self.active = False

        self.find_children()
        self.tap_num.set_text(str(tap_id))

    def set_description(self):
        if self.active:
            self.beer_description.set_markup("<b>{:.2f}</b> ounces poured".format(self.amount_poured))
        elif self.beer is not None:
            self.beer_description.set_text(self.beer.description)

    def update(self, tap):
        self.make_inactive()

        if tap["beer_id"] == self.beer_id:
            return

        try:
            beer = Beer.new_from_id(tap["beer_id"])
        except Exception as e:
            logging.error("Couldn't look up beer ID {}: {}".format(tap["beer_id"], e))
            return

        self.beer = beer

        self.beer_description.set_line_wrap(True)

        self.beer_name.set_text(beer.beer_name)
        self.beer_style.set_text(beer.beer_style)
        self.brewery_name.set_text(beer.brewery_name)
        self.brewery_loc.set_text(beer.brewery_loc)
        self.abv.set_text("{}%".format(beer.abv))

        self.load_image(self.brewery_label, beer.brewery_label)
        self.load_image(self.beer_label, beer.beer_label)

        self.pct_full_meter.set_fraction(tap["pct_full"])
        self.pct_full_meter.set_text("{}%".format(int(tap["pct_full"] * 100)))

        self.set_description()

    def update_active_tap(self, tap):
        self.amount_poured = tap.pulses * Config.get("units_per_pulse")

        if self.active:
            self.set_description()
            return

        logging.debug("making tap {} active".format(self.tap_id))
        self.active = True
        self.set_description()
        self.gtkobj.get_style_context().add_class("active")

    def make_inactive(self):
        if not self.active:
            return

        logging.debug("making tap {} inactive".format(self.tap_id))
        self.active = False
        self.amount_poured = None
        self.set_description()
        self.gtkobj.get_style_context().remove_class("active")


class CheckinDisplay(ObjectContainer):
    def __init__(self, gtkobj):
        super(CheckinDisplay, self).__init__()

        self.checkin_id = None
        self.gtkobj = gtkobj

        self.find_children()

    def update(self, checkin):
        if checkin.checkin_id == self.checkin_id:
            return

        self.checkin_id = checkin.checkin_id
        self.load_image(self.avatar, checkin.user_avatar)

        markup = "<b>{checkin.user_name}</b> enjoyed a <b>{checkin.beer.beer_name}</b> by <b>{checkin.beer.brewery_name}</b>\n<i>{checkin.time_since}</i>".format(checkin=checkin)
        self.description.set_line_wrap(True)
        self.description.set_markup(markup)


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

        self.tap_container = self.builder.get_object("TapDisplays")

        self.taps = dict()
        for tap in DB.get_taps():
            gtkobj = self.builder.get_object("TapEventBox_{}".format(tap["tap_id"]))
            self.taps[tap["tap_id"]] = TapDisplay(tap["tap_id"], gtkobj)

        self.checkin_displays = []
        for child in self.builder.get_object("UntappdBoxes").get_children():
            self.checkin_displays.append(CheckinDisplay(child))

        self.window.fullscreen()
        self.window.show_all()

    def update_taps(self):
        if self.kegmeter_status.interrupt_event.is_set():
            self.shutdown()
            return False

        if not self.kegmeter_status.tap_update_event.is_set():
            return True

        self.kegmeter_status.tap_update_event.clear()

        active_tap = self.kegmeter_status.get_active_tap()
        if active_tap is not None:
            self.tap_container.get_style_context().add_class("has_active")
            self.taps[active_tap.tap_id].update_active_tap(active_tap)
            return True

        self.tap_container.get_style_context().remove_class("has_active")
        for tap in DB.get_taps():
             self.taps[tap["tap_id"]].update(tap)

        return True

    def update_checkins(self):
        checkins = Checkin.get_latest()
        for checkin, display in zip(checkins, self.checkin_displays):
            display.update(checkin)

        return True

    def main(self):
        Gdk.threads_init()

        GObject.idle_add(self.update_taps)
        GObject.timeout_add(60000, self.update_checkins)

        self.update_checkins()

        Gtk.main()

    def shutdown(self):
        logging.error("Interface exiting")
        self.window.destroy()
        Gtk.main_quit()
