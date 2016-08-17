
import os
import sys
from setuptools import setup, find_packages
from shutil import rmtree
from cartridge import __version__ as version


exclude = ["cartridge/project_template/dev.db",
           "cartridge/project_template/project_name/local_settings.py"]
if sys.argv == ["setup.py", "test"]:
    exclude = []
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

if sys.argv[:2] == ["setup.py", "bdist_wheel"]:
    # Remove previous build dir when creating a wheel build,
    # since if files have been removed from the project,
    # they'll still be cached in the build dir and end up
    # as part of the build, which is really neat!
    try:
        rmtree("build")
    except:
        pass


try:
    setup(

        name="Cartridge",
        version=version,
        author="Stephen McDonald",
        author_email="stephen.mc@gmail.com",
        description="A Django shopping cart application.",
        long_description=open("README.rst", 'rb').read().decode('utf-8'),
        license="BSD",
        url="http://cartridge.jupo.org/",
        zip_safe=False,
        include_package_data=True,
        packages=find_packages(),
        test_suite="runtests.main",
        tests_require=["pyflakes>=0.6.1", "pep8>=1.4.1"],

        install_requires=[
            "mezzanine >= 4.2.0",
            "xhtml2pdf",
        ],
        extras_require={
            'stripe': ['stripe'],
        },

        classifiers=[
            "Development Status :: 4 - Beta",
            "Environment :: Web Environment",
            "Framework :: Django",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
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
