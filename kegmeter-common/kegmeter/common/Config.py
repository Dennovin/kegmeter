import os
import simplejson

class Config(object):
    settings = None
    base_dir = "/opt/kegmeter"

    @classmethod
    def get(cls, item):
        cls.parse()
        if item in cls.settings:
            return cls.settings[item]

    @classmethod
    def parse(cls):
        if cls.settings is not None:
            return

        config_file = os.path.join(cls.base_dir, "etc", "settings.json")
        with open(config_file, "r") as fh:
            contents = fh.read()
            cls.settings = simplejson.loads(contents)