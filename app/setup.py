from setuptools import setup, find_packages

setup(
    name="KegMeter",
    version="0.1",
    author="OmniTI Computer Consulting, Inc.",
    author_email="hello@omniti.com",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "memcache >= 1.53",
        "tornado >= 4.0",
        "oauth2client >= 1.3.1",
        ],
    )
