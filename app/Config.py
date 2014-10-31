import os
import simplejson

class Config(object):
    settings = None

    @classmethod
    def base_dir(cls):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)

    @classmethod
    def get(cls, item):
        cls.parse()
        return cls.settings[item]

    @classmethod
    def parse(cls):
        if cls.settings is not None:
            return

        config_file = os.path.join(cls.base_dir(), "config", "settings.json")
        with open(config_file, "r") as fh:
            contents = fh.read()
            cls.settings = simplejson.loads(contents)
