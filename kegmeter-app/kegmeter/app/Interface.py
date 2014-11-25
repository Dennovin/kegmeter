import logging
import os
import pkg_resources
import re
import requests
import threading
import time

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

from kegmeter.common import Config, Beer, Checkin, DBClient

mysterybeer_file = pkg_resources.resource_filename(__name__, "images/mysterybeer.png")


class ObjectContainer(object):
    images_loaded = dict()

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
        if url in self.images_loaded:
            image.set_from_pixbuf(self.images_loaded[url])
            return

        try:
            alloc = image.get_allocation()
            imgreq = requests.get(url)
            loader = GdkPixbuf.PixbufLoader.new_with_mime_type(imgreq.headers["content-type"])
            logging.debug(imgreq)
            loader.write(imgreq.content)
            pixbuf = loader.get_pixbuf()
            pixbuf = pixbuf.scale_simple(alloc.width, alloc.height, GdkPixbuf.InterpType.BILINEAR)
            image.set_from_pixbuf(pixbuf)
            self.images_loaded[url] = pixbuf
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
        if checkin.checkin_id != self.checkin_id:
            self.load_image(self.avatar, checkin.user_avatar)

        self.checkin_id = checkin.checkin_id

        markup = "<b>{checkin.user_name}</b> enjoyed a <b>{checkin.beer.beer_name}</b> by <b>{checkin.beer.brewery_name}</b>\n<i>{checkin.time_since}</i>".format(checkin=checkin)
        self.description.set_line_wrap(True)
        self.description.set_markup(markup)


class KegMeter(object):
    def __init__(self, kegmeter_status):
        self.kegmeter_status = kegmeter_status
        self.last_update = None
        self.last_checkin_update = None
        self.checkins = None

        self.builder = Gtk.Builder()
        self.builder.add_from_file(pkg_resources.resource_filename(__name__, "interface/interface.glade"))
        self.window = self.builder.get_object("OnTap")

        self.style_provider = Gtk.CssProvider()
        self.style_provider.load_from_path(pkg_resources.resource_filename(__name__, "interface/interface.css"))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.tap_container = self.builder.get_object("TapDisplays")

        self.taps = dict()
        for tap in DBClient.get_taps():
            gtkobj = self.builder.get_object("TapEventBox_{}".format(tap["tap_id"]))
            self.taps[tap["tap_id"]] = TapDisplay(tap["tap_id"], gtkobj)

        self.checkin_displays = []
        for child in self.builder.get_object("UntappdBoxes").get_children():
            self.checkin_displays.append(CheckinDisplay(child))

        self.window.fullscreen()
        self.window.show_all()

    def update_active_taps(self):
        self.tap_container.get_style_context().remove_class("has_active")

        for tap in self.kegmeter_status.tap_statuses.values():
            if tap.is_active():
                self.tap_container.get_style_context().add_class("has_active")
                self.taps[tap.tap_id].update_active_tap(tap)
            else:
                self.taps[tap.tap_id].make_inactive()

    def update_tap_info(self):
        for tap in DBClient.get_taps():
             self.taps[tap["tap_id"]].update(tap)

        return True

    def update_checkin_display(self):
        if self.checkins is not None:
            for checkin, display in zip(self.checkins, self.checkin_displays):
                display.update(checkin)

        return True

    def update_checkins(self):
        self.checkins = Checkin.get_latest()
        return True

    def main(self):
        Gdk.threads_init()

        GObject.timeout_add(1000, self.update_checkin_display)
        GObject.timeout_add(60000, self.update_tap_info)
        GObject.timeout_add(120000, self.update_checkins)

        self.update_listener_thread = threading.Thread(target=self.update_listener)
        self.update_listener_thread.daemon = True
        self.update_listener_thread.start()

        self.update_tap_info()
        self.update_checkins()

        Gtk.main()

    def shutdown(self):
        logging.error("Interface exiting")
        self.window.destroy()
        Gtk.main_quit()

    def update_listener(self):
        while not self.kegmeter_status.interrupt_event.is_set():
            self.kegmeter_status.tap_update_event.wait()
            self.kegmeter_status.tap_update_event.clear()
            GObject.idle_add(self.update_active_taps)

        self.shutdown()
