
import os, sys
from site import addsitedir

paths = ["..",".","apps","libs"]

def setup():

	dirname = os.path.abspath(os.path.join(os.path.dirname(
		os.path.abspath(__file__)), ".."))
	for path in paths:
		path = os.path.join(dirname, path)
		if path not in sys.path:
			sys.path.insert(0, path)
			package_paths = addsitedir(path, set())
			if package_paths:
				sys.path.extend(package_paths)

	os.environ['DJANGO_SETTINGS_MODULE'] = "%s.settings" % dirname.split(os.sep)[-1]
	
