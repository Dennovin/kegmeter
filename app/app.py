import argparse
import logging
import signal
import threading
import time

from Interface import KegMeter
from Serial import SerialListener
from Status import KegmeterStatus

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--no-interface", dest="no_interface", action="store_true",
                        help="Do not run interface.")
    parser.add_argument("--no-serial", dest="no_serial", action="store_true",
                        help="Do not run serial port listener.")
    parser.add_argument("--debug", dest="debug", action="store_true",
                        help="Display debugging information.")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    status = KegmeterStatus()

    signal.signal(signal.SIGINT, status.interrupt)

    if not args.no_interface:
        app = KegMeter(status)
        app_thread = threading.Thread(target=app.main)
        app_thread.start()

    if not args.no_serial:
        listener = SerialListener(status)
        listener_thread = threading.Thread(target=listener.listen)
        listener_thread.start()

    status.tap_update_event.set()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        status.interrupt()
    except:
        raise

    if not args.no_interface:
        app_thread.join()

    if not args.no_serial:
        listener_thread.join()
