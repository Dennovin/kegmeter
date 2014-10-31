import os
import sqlite3
import time

from Config import Config

class DB(object):
    db_file = os.path.join(Config.base_dir(), "db", "db.sql")
    schema_file = os.path.join(Config.base_dir(), "db", "schema.sql")

    @classmethod
    def connect(cls):
        return sqlite3.connect(cls.db_file)

    @classmethod
    def init_db(cls):
        db = cls.connect()
        with open(cls.schema_file, mode="r") as f:
            db.cursor().executescript(f.read())
            db.commit()

    @classmethod
    def get_taps(cls):
        taps = []

        cursor = cls.connect().cursor()
        cursor.execute("select tap_id, coalesce(beer_id, ''), last_updated, amount_poured from taps order by tap_id")

        for row in cursor:
            taps.append({
                    "tap_id": row[0],
                    "beer_id": row[1],
                    "last_updated": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row[2])),
                    "amount_poured": row[3] * Config.get("units_per_pulse"),
                    "pct_full": 1 - (row[3] * Config.get("units_per_pulse") / Config.get("total_keg_units")),
                    })

        cursor.close()

        return taps
