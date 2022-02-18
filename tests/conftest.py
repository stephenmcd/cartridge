import os
import shutil
import sys
import tempfile
from pathlib import Path

import django

# Path to the temp cartridge project folder
TMP_PATH = Path(tempfile.mkdtemp()) / "project_template"

TEST_SETTINGS = """
from . import settings

globals().update(i for i in settings.__dict__.items() if i[0].isupper())

# Add our own tests folder to installed apps (required to test models)
INSTALLED_APPS = list(INSTALLED_APPS)
INSTALLED_APPS.append("tests")

# Use the MD5 password hasher by default for quicker test runs.
PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)

# Add a currency locale
SHOP_CURRENCY_LOCALE = "en_US.UTF-8"

# Allowed development hosts
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "::1"]
"""


def pytest_report_header(config):
    """
    Have pytest report the path of the project folder
    """
    return f"cartridge proj (tmp): {TMP_PATH}"


def pytest_configure():
    """
    Hack the `project_template` dir into an actual project to test against.
    """
    from mezzanine.utils.importing import path_for_import

    template_path = Path(path_for_import("cartridge")) / "project_template"
    shutil.copytree(str(template_path), str(TMP_PATH))
    proj_path = TMP_PATH / "project_name"
    local_settings = (proj_path / "local_settings.py.template").read_text()
    (proj_path / "test_settings.py").write_text(TEST_SETTINGS + local_settings)

    # Setup the environment for Django
    sys.path.insert(0, str(TMP_PATH))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_name.test_settings")
    django.setup()


def pytest_unconfigure():
    """
    Remove the temporary folder
    """
    try:
        shutil.rmtree(str(TMP_PATH))
    except OSError:
        pass
