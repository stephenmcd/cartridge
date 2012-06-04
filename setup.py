
from __future__ import with_statement
import os

exclude = ["cartridge/project_template/dev.db",
           "cartridge/project_template/local_settings.py"]
exclude = dict([(e, None) for e in exclude])
for e in exclude:
    if e.endswith(".py"):
        try:
            os.remove("%sc" % e)
        except:
            pass
    try:
        with open(e, "r") as f:
            exclude[e] = (f.read(), os.stat(e))
        os.remove(e)
    except:
        pass

from setuptools import setup, find_packages

from cartridge import __version__ as version

try:
    setup(

        name="Cartridge",
        version=version,
        author="Stephen McDonald",
        author_email="stephen.mc@gmail.com",
        description="A Django shopping cart application.",
        long_description=open("README.rst").read(),
        license="BSD",
        url="http://cartridge.jupo.org/",
        zip_safe=False,
        include_package_data=True,
        packages=find_packages(),

        install_requires=[
            "mezzanine >= 1.1.1",
            "pisa >= 3.0.33",
        ],

        classifiers=[
            "Development Status :: 3 - Alpha",
            "Environment :: Web Environment",
            "Framework :: Django",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Topic :: Internet :: WWW/HTTP",
            "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
            "Topic :: Internet :: WWW/HTTP :: WSGI",
            "Topic :: Software Development :: Libraries :: "
                                                "Application Frameworks",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ])

finally:
    for e in exclude:
        if exclude[e] is not None:
            data, stat = exclude[e]
            try:
                with open(e, "w") as f:
                    f.write(data)
                os.chown(e, stat.st_uid, stat.st_gid)
                os.chmod(e, stat.st_mode)
            except:
                pass
