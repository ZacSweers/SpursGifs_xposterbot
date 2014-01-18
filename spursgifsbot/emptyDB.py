#!/usr/bin/env python

import pickle 		# dump list and dict to file
import os  			# OS-related stuff


def openDB(dbFile):
    if(os.path.isfile(dbFile)):
        f = open(dbFile, 'r+')

        # If the file isn't at its end or empty
        if f.tell() != os.fstat(f.fileno()).st_size:
            return pickle.load(f)
        f.close()


def saveDB(dbFile, data):
    f = open(dbFile, 'w+')
    pickle.dump(data, f)
    f.close()


print "(Cleaning Cache)"
db = "spursgifs_xposterDB"
print "\tOpening cache..."
already_done = openDB(db)
print "\tEmptying..."
del already_done[:]
saveDB(db, already_done)
assert len(openDB(db)) is 0
print "(Done emptying cache)"
