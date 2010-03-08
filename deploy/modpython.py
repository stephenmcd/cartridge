
from django.core.handlers.modpython import ModPythonHandler
from environment import setup

class CustomModPythonHandler(ModPythonHandler):

    def __call__(self, request):
        setup()
        return super(CustomModPythonHandler, self).__call__(request)

def handler(request):
    return CustomModPythonHandler()(request)
