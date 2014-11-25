import logging
import os
import pkg_resources
import sqlite3
import time

from kegmeter.common import Config

class DB(object):
    @classmethod
    def db_file(cls):
        return os.path.join(Config.base_dir, "db", "db.sql")

    schema_file = pkg_resources.resource_filename(__name__, "db/schema.sql")

    @classmethod
    def connect(cls):
        return sqlite3.connect(cls.db_file())

    @classmethod
    def init_db(cls):
        db = cls.connect()
        with open(cls.schema_file, mode="r") as f:
            db.cursor().executescript(f.read())
            db.commit()

    @classmethod
    def get_taps(cls):
        taps = []

        logging.debug("Getting taps from database")

        cursor = cls.connect().cursor()
        cursor.execute("select tap_id, coalesce(beer_id, ''), last_updated, last_updated_by, amount_poured from taps order by tap_id")

        for row in cursor:
            taps.append({
                    "tap_id": row[0],
                    "beer_id": row[1],
                    "last_updated": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row[2])),
                    "last_updated_by": row[3],
                    "amount_poured": row[4] * Config.get("units_per_pulse"),
                    "pct_full": 1 - (row[4] * Config.get("units_per_pulse") / Config.get("total_keg_units")),
                    })

        cursor.close()

        return taps

    @classmethod
    def get_temps(cls):
        temps = []

        cursor = cls.connect().cursor()
        cursor.execute("select sensor_id, deg_c from temperature order by sensor_id")

        for row in cursor:
            temps.append({
                    "sensor_id": row[0],
                    "deg_c": row[1],
                    })

        cursor.close()

        return temps

    @classmethod
    def update_amount_poured(cls, tap_id, pulses):
        logging.debug("Updating tap {} in database, {} pulses".format(tap_id, pulses))

        db = cls.connect()
        cursor = db.cursor()
        cursor.execute("insert into flowmeter(tap_id, flow_time, num_pulses) values(?, strftime('%s', 'now'), ?)", [tap_id, pulses])
        db.commit()

    @classmethod
    def update_temperature(cls, sensor_id, deg_c):
        logging.debug("Updating temperature on sensor {}, {} degrees".format(sensor_id, deg_c))

        db = cls.connect()
        cursor = db.cursor()
        cursor.execute("insert or replace into temperature(sensor_id, deg_c, last_reading) values(?, ?, strftime('%s', 'now'))", [sensor_id, deg_c])
        db.commit()

