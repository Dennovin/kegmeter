from setuptools import setup, find_packages

setup(
    name="kegmeter",
    version="0.1",
    author="OmniTI Computer Consulting, Inc.",
    author_email="hello@omniti.com",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "oauth2client >= 1.3.1",
        "pygobject >= 3.8.2",
        "pyserial >= 2.7",
        "pysqlite >= 2.6.3",
        "python-memcached >= 1.53",
        "requests >= 1.2.3",
        "simplejson >= 3.6.5",
        "tornado >= 4.0.2",
        ],
    )
