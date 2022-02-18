"""
This is the local_settings file for Cartridge's docs.
"""

from random import choice

from cartridge.project_template.project_name.settings import *  # noqa: F401, F403

ROOT_URLCONF = "cartridge.project_template.project_name.urls"

# Generate a SECRET_KEY for this build

characters = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
SECRET_KEY = "".join([choice(characters) for i in range(50)])
