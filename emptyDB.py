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


db = "spursgifs_xposterDB"
already_done = openDB(db)
del already_done[:]
saveDB(db, already_done)
assert len(openDB(db)) is 0
