"""
Based on what I learned creeping the source code for
https://github.com/cris9696/PlayStoreLinks_Bot
"""

import praw  		# reddit wrapper
import time 		# obvious
import pickle 		# dump list and dict to file
import os  			# OS-related stuff
import sys 			# ""
import atexit 		# To handle unexpected crashes or just normal exiting
import logging 		# logging

# DB for caching previous posts
dbFile = "spursgifs_xposterDB"

# File with login credentials
propsFile = "login.txt"

# flag to check if db file's already checked
fileOpened = False


# Called when exiting the program
def exit_handler():
    if fileOpened:
        pickle.dump(already_done, f)
        f.close()
        # pickle.dump(nameLinkDict, fi)
        # fi.close()
    print("Shutting Down")
    os.remove("theBotIsRunning")

# Register the function that get called on exit
atexit.register(exit_handler)


# Function to exit the bot
def exitBot():
    sys.exit()


# Submission
def submit(subreddit, title, link):
    try:
        if r.get_info(url=link):
            print "Already submitted"
            already_done.append(submission.id)
            return
        subreddit.submit(title + " (x-post from /r/coys)", url=link)
    except praw.errors.APIException:
        logging.exception("Error on link submission.")


# Retrieves the extension
def extension(url):
    return os.path.splitext(url)[1]


# Validates if a submission should be posted
def validateSubmission(submission, ):
    if submission.id not in already_done and \
        (submission.domain in allowedDomains or
         extension(submission.url) in allowedExtensions):
        return True
    return False

# If the bot is already running
if(os.path.isfile('theBotIsRunning')):
    print("The bot is already running, shutting down")
    exitBot()

# The bot was not running
# create the file that tell the bot is running
open('theBotIsRunning', 'w').close()


try:
    # reading login info from a file, it should be username (newline)
    # password
    with open("login.properties", "r") as loginFile:
        loginInfo = loginFile.readlines()

    loginInfo[0] = loginInfo[0].replace('\n', '')
    loginInfo[1] = loginInfo[1].replace('\n', '')

    r = praw.Reddit('/u/spursgifs_xposterbot by /u/pandanomic')
    r.login(loginInfo[0], loginInfo[1])

    # read off /r/coys
    coys_subreddit = r.get_subreddit('coys')

    # submit to /r/SpursGifs
    spursgifs_subreddit = r.get_subreddit('SpursGifs')
except:
    exitBot()

print("Logged in")

allowedDomains = ["gfycat.com", "vine.co"]
allowedExtensions = [".gif"]

# Array with previously linked posts
# Check the db cache first
already_done = []
if(os.path.isfile(dbFile)):
    f = open(dbFile, 'r+')

    # If the file isn't at its end or empty
    if f.tell() != os.fstat(f.fileno()).st_size:
        already_done = pickle.load(f)
    f.close()
f = open(dbFile, 'w+')

print already_done
del already_done[:]

fileOpened = True

while True:
    for submission in coys_subreddit.get_hot(limit=10):
        if validateSubmission(submission):
            # already_done.append(submission.id)
            print "Allowed: " + submission.title
    print 'Looped'
    time.sleep(60)

# submit(spursgifs_subreddit, "Test", "http://i.imgur.com/zlCgjl2.gif")

# for submission in coys_subreddit.get_hot(limit=10):
#     if validateSubmission(submission):
#         print "Allowed: " + submission.title
