#!/usr/bin/env python

"""
Based on what I learned creeping the source code for
https://github.com/cris9696/PlayStoreLinks_Bot
"""
import time         # obvious
import pickle       # dump list and dict to file
import os           # OS-related stuff
import sys          # ""
import atexit       # To handle unexpected crashes or just normal exiting
import logging      # logging
import signal       # Catch SIGINT
import string       # Used in generating random strings
import random       # ""
import urllib       # For encoding urls
import subprocess   # To send shell commands, used for local testing
import praw         # reddit wrapper
import requests     # For URL requests, ued in gfycat API


# tagline
commentTag = """------

*Hi! I'm a bot created to x-post gifs/vines/gfycats from /r/coys over to /r/SpursGifs.*

*Feedback/bug reports? Send a message to [pandanomic](http://www.reddit.com/message/compose?to=pandanomic).*

*[Source code](https://github.com/pandanomic/SpursGifs_xposterbot)*"""

# DB for caching previous posts
dbFile = "spursgifs_xposterDB"

# File with login credentials
propsFile = "login.properties"

# flag to check if db file's already checked
fileOpened = False

# subreddit to x-post to. Changes if testing
postSub = "SpursGifs"

# for cron jobs
cron = False

# for my mac, I use terminal-notifier to get updates
macUpdate = False

# for keeping track of if we're on Heroku
running_on_heroku = False

if os.environ.get('MEMCACHEDCLOUD_SERVERS', None):
    import bmemcached

    print '\tRunning on heroku, using memcached'

    running_on_heroku = True
    mc = bmemcached.Client(os.environ.get('MEMCACHEDCLOUD_SERVERS').split(','),
                           os.environ.get('MEMCACHEDCLOUD_USERNAME'),
                           os.environ.get('MEMCACHEDCLOUD_PASSWORD'))


# Called when exiting the program
def exit_handler():
    print "(SHUTTING DOWN)"
    if not running_on_heroku and fileOpened:
        pickle.dump(already_done, f)
        f.close()
    os.remove("BotRunning")


# Called on SIGINT
# noinspection PyUnusedLocal
def signal_handler(input_signal, frame):
    print '\n(Caught SIGINT, exiting gracefully)'
    sys.exit()

# Register the function that get called on exit
atexit.register(exit_handler)

# Register function to call on SIGINT
signal.signal(signal.SIGINT, signal_handler)


# Function to exit the bot
def exit_bot():
    sys.exit()


# Check cache for string
def check_cache(input_key):
    print '\tChecking cache for ' + str(input_key)
    if running_on_heroku:
        obj = mc.get(str(input_key))
        if not obj or obj != "True":
            return False
        else:
            return True
    if input_key in already_done:
        return True
    return False


# Cache a key (original url, gfy url, or submission id)
def cache_key(input_key):
    if running_on_heroku:
        mc.set(str(input_key), "True")
        assert str(mc.get(str(input_key))) == "True"
    else:
        already_done.append(input_key)

    print '\tCached ' + str(input_key)


# Remove an item from caching
def cache_remove_key(input_submission):
    print "\t--Rate Limit Exceeded"
    if running_on_heroku:
        mc.delete(str(input_submission.id))
        mc.delete(str(input_submission.url))
    else:
        already_done.remove(input_submission.id)
        already_done.remove(input_submission.url)

    print '\tDeleted ' + str(input_submission.id)


# Main bot runner
def bot():
    print "(Parsing new 30)"
    new_count = 0
    for submission in coys_subreddit.get_new(limit=30):
        if validate_submission(submission):
            new_count += 1

            print "(New Post)"
            submit(spursgifs_subreddit, submission)

    if new_count == 0:
        print "(Nothing new)"


# Submission
def submit(subreddit, submission):
    if macUpdate:
        print '\tNotifying on Mac'
        try:
            subprocess.call(
                ["terminal-notifier", "-message", "New post", "-title",
                 "Spurs Gif Bot", "-sound", "default"])
        except OSError:
            print '\t--Could not find terminal-notifier, please reinstall'

    url_to_submit = submission.url
    gfy_converted = False

    # Convert if it's a gif
    if extension(submission.url) == ".gif":
        new_url_to_submit = gfycat_convert(url_to_submit)
        if new_url_to_submit != "Error":
            # Cache the new gfy url and submit it instead
            cache_key(new_url_to_submit)
            url_to_submit = new_url_to_submit
            gfy_converted = True

    print "\tSubmitting to /r/" + postSub + "..."
    try:
        new_submission = subreddit.submit(
            submission.title + " (x-post from /r/coys)", url=url_to_submit)

        # Cache on successful submission
        cache_key(submission.id)
        cache_key(submission.url)

        followup_comment(submission, new_submission, gfy_converted)

    except praw.errors.AlreadySubmitted:
        print "\t--Already submitted, caching"
        # Cache stuff
        cache_key(submission.id)
        cache_key(submission.url)

    except praw.errors.RateLimitExceeded:
        cache_remove_key(submission)

    except praw.errors.APIException:
        logging.exception("Error on link submission.")


# Retrieves the extension
def extension(url):
    return os.path.splitext(url)[1]


# Validates if a submission should be posted
def validate_submission(submission):
    # check domain and extension validity
    if submission.domain in allowedDomains or extension(
            submission.url) in allowedExtensions:
        # Check for submission id and url
        return not (check_cache(submission.id) or check_cache(submission.url))
    return False


# Followup Comment
def followup_comment(submission, new_submission, gfy_converted):
    print("\tFollowup Comment...")
    followup_comment_text = "Originally posted [here](" + \
                            submission.permalink + ") by /u/" + \
                            submission.author.name + \
                            ".\n\n"
    followup_comment_text += commentTag

    try:
        new_submission.add_comment(followup_comment_text)
        notify_comment(new_submission.permalink, submission, gfy_converted)
    except praw.errors.RateLimitExceeded:
        print "\t--Rate Limit Exceeded"
    except praw.errors.APIException:
        logging.exception("Error on followupComment")


# Notifying comment
def notify_comment(new_url, submission, gfy_converted):
    print("\tNotify Comment...")
    notify_comment_text = "X-posted to [here](" + new_url + ").\n\n"
    notify_comment_text += commentTag

    if gfy_converted:
        notify_comment_text = "Converted to gfycat and x" + \
                              notify_comment_text[1::]

    try:
        submission.add_comment(notify_comment_text)
    except praw.errors.RateLimitExceeded:
        print "\t--Rate Limit Exceeded"
    except praw.errors.APIException:
        logging.exception("Error on notifyComment")


# Login
def retrieve_login_credentials(login_type):
    if login_type == "propFile":
        # reading login info from a file, it should be username \n password
        print "\t--Reading login.properties"
        with open("login.properties", "r") as loginFile:
            login_info = loginFile.readlines()

        login_info[0] = login_info[0].replace('\n', '')
        login_info[1] = login_info[1].replace('\n', '')
        return login_info
    if login_type == "env":
        print "\t--Reading env variables"
        login_info = [os.environ['REDDIT_USERNAME'],
                      os.environ['REDDIT_PASSWORD']]
        return login_info


# Generate a random 10 letter string
# Borrowed from here: http://stackoverflow.com/a/16962716/3034339
def gen_random_string():
    return ''.join(random.sample(string.letters * 10, 10))


# Convert gifs to gfycat
def gfycat_convert(url_to_convert):
    print '\tConverting gif to gfycat'
    encoded_url = urllib.quote(url_to_convert, '')

    # Convert
    url_string = 'http://upload.gfycat.com/transcode/' + gen_random_string() + \
                 '?fetchUrl=' + encoded_url
    conversion_response = requests.get(url_string)
    if conversion_response.status_code == 200:
        print '\t--success'
        j = conversion_response.json()
        gfyname = j["gfyname"]
        return "http://gfycat.com/" + gfyname
    else:
        print '\t--failed'
        return "Error"


# If the bot is already running
if os.path.isfile('BotRunning'):
    print("The bot is already running, shutting down")
    exit_bot()

# The bot was not running
# create the file that tell the bot is running
open('BotRunning', 'w').close()

print "(Starting Bot)"

print "(OS is " + sys.platform + ")"

args = sys.argv
loginType = "propFile"

if len(args) > 1:
    print "\tGetting args..."
    if "--testing" in args:
        postSub = "pandanomic_testing"
    if "--cron" in args:
        cron = True
    if "--env" in args:
        loginType = "env"
    if "--notify" in args and sys.platform == "darwin":
        macUpdate = True
    print "\t(Args: " + str(args[1:]) + ")"

r = praw.Reddit('/u/spursgifs_xposterbot by /u/pandanomic')

try:
    print "\tLogging in via " + loginType + "..."
    loginInfo = retrieve_login_credentials(loginType)
    r.login(loginInfo[0], loginInfo[1])

except praw.errors:
    print "LOGIN FAILURE"
    exit_bot()

# read off /r/coys
coys_subreddit = r.get_subreddit('coys')

# submit to /r/SpursGifs or /r/pandanomic_testing
spursgifs_subreddit = r.get_subreddit(postSub)

allowedDomains = ["gfycat.com", "vine.co", "giant.gfycat.com", "fitbamob.com"]
allowedExtensions = [".gif"]

# Array with previously linked posts
# Check the db cache first
already_done = []
if not running_on_heroku:
    print "\tChecking cache..."
    if os.path.isfile(dbFile):
        f = open(dbFile, 'r+')

        # If the file isn't at its end or empty
        if f.tell() != os.fstat(f.fileno()).st_size:
            already_done = pickle.load(f)
        f.close()
    f = open(dbFile, 'w+')

    print '(Cache size: ' + str(len(already_done)) + ")"

# noinspection PyRedeclaration
fileOpened = True

counter = 0

if cron:
    print "(Cron job)"
    bot()
else:
    print "(Looping)"
    while True:
        bot()
        counter += 1
        print '(Looped - ' + str(counter) + ')'
        time.sleep(60)
