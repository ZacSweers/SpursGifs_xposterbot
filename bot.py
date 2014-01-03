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
propsFile = "login.properties"

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
    os.remove("BotRunning")

# Register the function that get called on exit
atexit.register(exit_handler)


# Function to exit the bot
def exitBot():
    sys.exit()


# Submission
def submit(subreddit, submission):
    print("(Submitting)")
    try:
        subreddit.submit(
            submission.title + " (x-post from /r/coys)", url=submission.url)
        followupComment(submission)
    except praw.errors.AlreadySubmitted:
        # logging.exception("Already submitted")
        print "(Already submitted)"
        if submission.id not in already_done:
            already_done.append(submission.id)
    except praw.errors.RateLimitExceeded:
        print "(Rate Limit Exceeded)"
        already_done.remove(submission.id)
    except praw.errors.APIException:
        logging.exception("Error on link submission.")


# Retrieves the extension
def extension(url):
    return os.path.splitext(url)[1]


# Validates if a submission should be posted
def validateSubmission(submission):
    if submission.id not in already_done and \
        (submission.domain in allowedDomains or
         extension(submission.url) in allowedExtensions):
        return True
    return False


# Followup Comment
def followupComment(submission):
    print("(Followup Comment)")
    user = r.get_redditor("spursgifs_xposterbot")
    newSubmission = user.get_submitted(limit=1).next()
    followupCommentText = "Originally posted by /u/" + \
        submission.author.fullname + \
        " [here](" + submission.permalink + ").\n\n"

    # TODO: Extract this to a global variable
    followupCommentText += "------\n\n"
    followupCommentText += "*Hi! I'm a bot created to x-posting gifs/vines/gfycats from /r/coys over to /r/SpursGifs.*\n\n"
    followupCommentText += "*Feedback/bug reports? Send a message to [pandanomic](http://www.reddit.com/message/compose?to=pandanomic).*\n\n"
    followupCommentText += "*[Source code](https://github.com/pandanomic/SpursGifs_xposterbot)*"

    try:
        newSubmission.add_comment(followupCommentText)
        notifyComment(newSubmission.permalink, submission)
    except praw.errors.RateLimitExceeded:
        print "(Rate Limit Exceeded)"
    except praw.errors.APIException:
        logging.exception("Error on followupComment")


# Notifying comment
def notifyComment(newURL, submission):
    print("(Notify Comment)")
    notifyCommentText = "X-posted to [here](" + newURL + ").\n\n"
    notifyCommentText += "------\n\n"
    notifyCommentText += "*Hi! I'm a bot created to x-posting gifs/vines/gfycats from /r/coys over to /r/SpursGifs.*\n\n"
    notifyCommentText += "*Feedback/bug reports? Send a message to [pandanomic](http://www.reddit.com/message/compose?to=pandanomic).*\n\n"
    notifyCommentText += "*[Source code](https://github.com/pandanomic/SpursGifs_xposterbot)*"

    try:
        submission.add_comment(notifyCommentText)
    except praw.errors.RateLimitExceeded:
        print "(Rate Limit Exceeded)"
    except praw.errors.APIException:
        logging.exception("Error on notifyComment")

# If the bot is already running
if(os.path.isfile('BotRunning')):
    print("The bot is already running, shutting down")
    exitBot()

# The bot was not running
# create the file that tell the bot is running
open('BotRunning', 'w').close()

print "(Starting)"

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

    # submit to testing
    # spursgifs_subreddit = r.get_subreddit('pandanomic_testing')
except:
    exitBot()

print("(Logged in)")

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

print '(Cache size: ' + str(len(already_done)) + ")"

fileOpened = True

counter = 0
while True:
    print "(Parsing top 20)"
    for submission in coys_subreddit.get_hot(limit=20):
        if validateSubmission(submission):
            already_done.append(submission.id)
            submit(spursgifs_subreddit, submission)
    print '(Looped - ' + str(counter) + ')'
    counter += 1
    time.sleep(60)
