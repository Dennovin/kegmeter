import os
from setuptools import setup, find_packages

setup(
    name="kegmeter-web",
    description="Kegmeter web server",
    url="https://github.com/Dennovin/kegmeter",
    version="0.99.0",
    author="OmniTI Computer Consulting, Inc.",
    author_email="hello@omniti.com",
    license="MIT",
    namespace_packages=["kegmeter"],
    packages=find_packages(),
    package_data={
        "kegmeter.web": ["static/*", "templates/*", "db/*"],
        },
    install_requires=[
        "kegmeter-common >= 0.1",
        "pycrypto >= 2.6.1",
        "pysqlite >= 2.6.3",
        "tornado >= 4.0.2",
        ],
    scripts=[
        "scripts/kegmeter_web.py",
        ],
    )
