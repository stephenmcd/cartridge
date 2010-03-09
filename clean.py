
from os import walk, remove, rmdir
from os.path import dirname, join, splitext, sep, abspath
from sys import argv


types = ("ALL", "svn", "pyc")


argv = argv[1:]
if not argv:
    index = -1
    while True:
        try:
            index = int(raw_input("\nChoose an extension type for removal:\n\n%s\n\n" % 
                "\n".join(["[%s] %s" % (i, type) for i, type in enumerate(types)])))
            if index in range(len(types)):
                if index == 0:
                    argv = types[1:]
                else:
                    argv = [types[index]]
                break
        except Exception, e:
            pass
        print "\nInvalid selection"

print __file__
for root, dirs, files in walk(dirname(abspath(__file__)), False):
    for ext in argv:
        ext = ".%s" % ext
        in_dir = ext in root.split(sep)
        for d in dirs:
            if in_dir or d == ext:
                d = join(root, d)
                print "deleting %s" % d
                rmdir(d)
        for f in files:
            if in_dir or splitext(f)[1].lower() == ext:
                f = join(root, f)
                print "deleting %s" % f
                remove(f)
