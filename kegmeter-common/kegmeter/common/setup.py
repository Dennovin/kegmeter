import os
from setuptools import setup, find_packages

setup(
    name="kegmeter-common",
    version="0.1",
    author="OmniTI Computer Consulting, Inc.",
    author_email="hello@omniti.com",
    license="MIT",
    packages=["kegmeter.common"],
    package_dir={"kegmeter.common": "."},
    install_requires=[
        "ago >= 0.0.6",
        "oauth2client >= 1.3.1",
        "pysqlite >= 2.6.3",
        "python-memcached >= 1.53",
        "requests >= 1.2.3",
        "simplejson >= 3.6.5",
        "tornado >= 4.0.2",
        ],
    scripts=[
        "kegmeter_web.py",
        ],
    )
