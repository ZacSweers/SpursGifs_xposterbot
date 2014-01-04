#!/usr/bin/env python

"""
This is just a script for cleaning up my testing subreddit.
"""

import praw

print "(Cleaning Up Testing Sub)"
print "\tLogging in..."
# reading login info from a file, it should be username (newline) password
with open("login.properties", "r") as loginFile:
    loginInfo = loginFile.readlines()

loginInfo[0] = loginInfo[0].replace('\n', '')
loginInfo[1] = loginInfo[1].replace('\n', '')

r = praw.Reddit('/u/spursgifs_xposterbot testing cleanup')
r.login(loginInfo[0], loginInfo[1])

print "\tGetting posts..."
# submit to /r/SpursGifs or /r/pandanomic_testing
testingSub = r.get_subreddit('pandanomic_testing')
allPosts = testingSub.get_top_from_all()

count = 1
for submission in allPosts:
    print "\tDeleting " + submission.id
    flat_comments = praw.helpers.flatten_tree(submission.comments)
    for comment in flat_comments:
        comment.delete()
    submission.delete()

print "(Done Cleaning)"
