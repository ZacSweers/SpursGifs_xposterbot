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
import pyquery      # For parsing vine html


# Color class, used for colors in terminal
class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


# tagline
commentTag = """------

*Hi! I'm a bot created to x-post gifs/vines/gfycats to /r/SpursGifs.*

*Feedback/bug reports? Send a message to
[pandanomic](http://www.reddit.com/message/compose?to=pandanomic).*

*[Source code](https://github.com/pandanomic/SpursGifs_xposterbot)*"""

# DB for caching previous posts
cache_file = "spursgifs_xposterDB"

# File with login credentials
propsFile = "login.properties"

# subreddit to x-post to. Changes if testing
postSub = "SpursGifs"

# for my mac, I use terminal-notifier to get updates
macUpdate = False

# for keeping track of if we're on Heroku
running_on_heroku = False


# Log method. If there's a color argument, it'll stick that in first
def log(message, *colorargs):
    if len(colorargs) > 0:
        print colorargs[0] + message + Color.END
    else:
        print message


# Called when exiting the program
def exit_handler():
    log("(SHUTTING DOWN)", Color.BOLD)
    if not running_on_heroku:
        with open(cache_file, 'r+') as db_file_save:
            pickle.dump(already_done, db_file_save)
    os.remove("BotRunning")


# Called on SIGINT
# noinspection PyUnusedLocal
def signal_handler(input_signal, frame):
    log('\n(Caught SIGINT, exiting gracefully)', Color.RED)
    sys.exit()


# Function to exit the bot
def exit_bot():
    sys.exit()


# Check cache for string
def check_cache(input_key):
    log('--Checking cache for ' + str(input_key))
    if running_on_heroku:
        obj = mc.get(str(input_key))
        if not obj or obj != "True":
            return False
        else:
            return True
    else:
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

    log('--Cached ' + str(input_key), Color.GREEN)


# Remove an item from caching
def cache_remove_key(input_submission):
    log("--Removing from cache", Color.RED)
    if running_on_heroku:
        mc.delete(str(input_submission.id))
        mc.delete(str(input_submission.url))
    else:
        already_done.remove(input_submission.id)
        already_done.remove(input_submission.url)

    log('--Deleted ' + str(input_submission.id), Color.RED)


# Main bot runner
def bot():
    log("(Parsing new 30)")
    new_count = 0
    for submission in coys_subreddit.get_new(limit=30):
        if not check_cache(submission.id):
            if validate_submission(submission):
                new_count += 1

                log("(New Post)", Color.GREEN)
                submit(spursgifs_subreddit, submission)
            else:
                cache_key(submission.id)

    if new_count == 0:
        log("(Nothing new)", Color.BOLD)


# Submission
def submit(subreddit, submission):
    if macUpdate:
        log('Notifying on Mac', Color.BOLD)
        try:
            subprocess.call(
                ["terminal-notifier", "-message", "New post", "-title",
                 "Spurs Gif Bot", "-sound", "default"])
        except OSError:
            log('--Could not find terminal-notifier, please reinstall', Color.RED)

    url_to_submit = submission.url
    gfy_converted = False

    # Convert if it's a gif
    if extension(submission.url) == ".gif" or submission.domain == 'vine.co':

        if submission.domain == 'vine.co':
            url_to_submit = retrieve_vine_video_url(url_to_submit)

        new_url_to_submit = gfycat_convert(url_to_submit)
        if new_url_to_submit != "Error":
            # Cache the new gfy url and submit it instead
            cache_key(new_url_to_submit)
            url_to_submit = new_url_to_submit
            gfy_converted = True

    log("--Submitting to /r/" + postSub)
    try:
        new_submission = subreddit.submit(
            submission.title + " (x-post from /r/coys)", url=url_to_submit)

        # Cache on successful submission
        cache_key(submission.id)
        cache_key(submission.url)

        followup_comment(submission, new_submission, gfy_converted)

    except praw.errors.AlreadySubmitted:
        log("----Already submitted, caching", Color.RED)
        # Cache stuff
        cache_key(submission.id)
        cache_key(submission.url)

    except praw.errors.RateLimitExceeded:
        log('--Rate limit exceeded', Color.RED)
        cache_remove_key(submission)

    except praw.errors.APIException:
        log('--API exception', Color.RED)
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
    log("--Followup Comment")
    followup_comment_text = "Originally posted [here](" + \
                            submission.permalink + ") by /u/" + \
                            submission.author.name + \
                            ".\n\n"
    followup_comment_text += commentTag

    try:
        new_submission.add_comment(followup_comment_text)
        notify_comment(new_submission.permalink, submission, gfy_converted)
    except praw.errors.RateLimitExceeded:
        log("--Rate Limit Exceeded", Color.RED)
    except praw.errors.APIException:
        log('--API exception', Color.RED)
        logging.exception("Error on followupComment")


# Notifying comment
def notify_comment(new_url, submission, gfy_converted):
    log("--Notify Comment", Color.RED)
    notify_comment_text = "X-posted to [here](" + new_url + ").\n\n"
    notify_comment_text += commentTag

    if gfy_converted:
        notify_comment_text = "Converted to gfycat and x" + \
                              notify_comment_text[1::]

    try:
        submission.add_comment(notify_comment_text)
    except praw.errors.RateLimitExceeded:
        log("--Rate Limit Exceeded", Color.RED)
    except praw.errors.APIException:
        log('--API exception', Color.RED)
        logging.exception("Error on followupComment")


# Login
def retrieve_login_credentials():
    if running_on_heroku:
        login_info = [os.environ['REDDIT_USERNAME'],
                      os.environ['REDDIT_PASSWORD']]
        return login_info
    else:
        # reading login info from a file, it should be username \n password
        with open("login.properties", "r") as loginFile:
            login_info = loginFile.readlines()

        login_info[0] = login_info[0].replace('\n', '')
        login_info[1] = login_info[1].replace('\n', '')
        return login_info


# Generate a random 10 letter string
# Borrowed from here: http://stackoverflow.com/a/16962716/3034339
def gen_random_string():
    return ''.join(random.sample(string.letters * 10, 10))


# Returns the .mp4 url of a vine video
def retrieve_vine_video_url(vine_url):
    log('--Converting vine to gfycat')
    d = pyquery.PyQuery(url=vine_url)
    video_url = d("meta[property=twitter\\:player\\:stream]").attr['content']
    video_url = video_url.partition("?")[0]
    return video_url


# Convert gifs to gfycat
def gfycat_convert(url_to_convert):
    log('--Converting gif to gfycat')
    encoded_url = urllib.quote(url_to_convert, '')

    # Convert
    url_string = 'http://upload.gfycat.com/transcode/' + gen_random_string() + \
                 '?fetchUrl=' + encoded_url
    conversion_response = requests.get(url_string)
    if conversion_response.status_code == 200:
        log('----success', Color.GREEN)
        j = conversion_response.json()
        gfyname = j["gfyname"]
        return "http://gfycat.com/" + gfyname
    else:
        log('----failed', Color.RED)
        return "Error"


# Main method
if __name__ == "__main__":
    # If the bot is already running
    if os.path.isfile('BotRunning'):
        log("The bot is already running, shutting down", Color.RED)
        exit_bot()

    if os.environ.get('MEMCACHEDCLOUD_SERVERS', None):
        import bmemcached

        log('Running on heroku, using memcached', Color.BOLD)

        running_on_heroku = True
        mc = bmemcached.Client(os.environ.get('MEMCACHEDCLOUD_SERVERS').
                               split(','),
                               os.environ.get('MEMCACHEDCLOUD_USERNAME'),
                               os.environ.get('MEMCACHEDCLOUD_PASSWORD'))

    # Register the function that get called on exit
    atexit.register(exit_handler)

    # Register function to call on SIGINT
    signal.signal(signal.SIGINT, signal_handler)

    # The bot was not running
    # create the file that tell the bot is running
    open('BotRunning', 'w').close()

    log("Starting Bot", Color.BOLD)

    log("OS is " + sys.platform, Color.BOLD)

    args = sys.argv
    loginType = "propFile"

    if len(args) > 1:
        log("Getting args", Color.BOLD)
        if "--testing" in args:
            postSub = "pandanomic_testing"
        if "--notify" in args and sys.platform == "darwin":
            macUpdate = True
        log("--(Args: " + str(args[1:]) + ")", Color.BOLD)

    r = praw.Reddit('/u/spursgifs_xposterbot by /u/pandanomic')

    try:
        log("Retrieving login credentials", Color.BOLD)
        loginInfo = retrieve_login_credentials()
        r.login(loginInfo[0], loginInfo[1])
        log("--Login successful", Color.GREEN)

    except praw.errors:
        log("LOGIN FAILURE", Color.RED)
        exit_bot()

    # read off /r/coys
    coys_subreddit = r.get_subreddit('coys')

    # submit to /r/SpursGifs or /r/pandanomic_testing
    spursgifs_subreddit = r.get_subreddit(postSub)

    allowedDomains = ["gfycat.com", "vine.co", "giant.gfycat.com",
                      "fitbamob.com"]

    allowedExtensions = [".gif"]

    # Array with previously linked posts
    # Check the db cache first
    already_done = []
    if not running_on_heroku:
        log("Loading cache", Color.BOLD)
        if os.path.isfile(cache_file):
            with open(cache_file, 'r+') as db_file_load:
                already_done = pickle.load(db_file_load)

        log('--Cache size: ' + str(len(already_done)))

    counter = 0

    if running_on_heroku:
        log("Heroku run", Color.BOLD)
        bot()
    else:
        log("Looping", Color.BOLD)
        while True:
            bot()
            counter += 1
            log('Looped - ' + str(counter), Color.BOLD)
            time.sleep(60)
