import logging
import threading

from Interface import KegMeter

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    update_event = threading.Event()

    app = KegMeter()
    app.update_event = update_event
    app_thread = threading.Thread(target=app.main)
    app_thread.start()

    update_event.set()

    app_thread.join()
