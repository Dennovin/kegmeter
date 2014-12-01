#!/usr/bin/env python

import argparse
import logging
import signal
import sys

from kegmeter.common import Config
from kegmeter.web import DB, WebServer

def run_webserver():
    logging.basicConfig(format="%(asctime)-15s %(message)s")

    parser = argparse.ArgumentParser()

    parser.add_argument("--init-db", dest="init_db", action="store_true",
                        help="Initialize database and exit.")
    parser.add_argument("--base-dir", dest="base_dir",
                        help="Specify base directory.")
    parser.add_argument("--debug", dest="debug", action="store_true",
                        help="Display debugging information.")
    parser.add_argument("--logfile", dest="logfile",
                        help="Output to log file instead of STDOUT.")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.logfile:
        logging.basicConfig(filename=args.logfile)

    if args.base_dir:
        Config.base_dir = args.base_dir

    if args.init_db:
        DB.init_db()
        sys.exit(0)

    webserver = WebServer()
    webserver.listen()


if __name__ == "__main__":
    run_webserver()
