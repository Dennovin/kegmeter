from setuptools import setup, find_packages

setup(
    name="kegmeter-app",
    description="Kegmeter libraries used by both the app and the webserver",
    url="https://github.com/Dennovin/kegmeter",
    version="0.99.8",
    author="OmniTI Computer Consulting, Inc.",
    author_email="hello@omniti.com",
    namespace_packages=["kegmeter"],
    license="MIT",
    packages=find_packages(),
    package_data={
        "kegmeter.app": ["interface/*", "images/*"],
        },
    install_requires=[
        "kegmeter-common >= 0.20",
        "ago >= 0.0.6",
        "pillow >= 2.6.1",
        "pyserial >= 2.7",
        "requests >= 1.2.3",
        "simplejson >= 3.6.5",
        ],
    scripts=[
        "scripts/kegmeter_app.py",
        ],
    )
