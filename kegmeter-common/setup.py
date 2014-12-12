import os
from setuptools import setup, find_packages

setup(
    name="kegmeter-common",
    description="Kegmeter libraries used by both the app and the webserver",
    url="https://github.com/Dennovin/kegmeter",
    version="0.99.0",
    author="OmniTI Computer Consulting, Inc.",
    author_email="hello@omniti.com",
    license="MIT",
    namespace_packages=["kegmeter"],
    packages=find_packages(),
    install_requires=[
        "ago >= 0.0.6",
        "oauth2client >= 1.3.1",
        "python-memcached >= 1.53",
        "requests >= 1.2.3",
        "simplejson >= 3.6.5",
        ],
    )
