#!C:/Python27/python.exe -u
# -*- coding: UTF-8 -*-

print "Content-Type: text/html"
print

import cgitb
cgitb.enable()
# Log errors to file
# cgitb.enable(display=0, logdir="/cgi-bin/")

import os
import cgi
import json
import pprint
import logging

logger = logging.getLogger(__name__)
logging_level = logging.DEBUG


def initliaze_logging():
    handler = logging.FileHandler('log.txt')
    handler.setLevel(logging_level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.setLevel(logging_level)
    logger.addHandler(handler)


class github_event(object):
    """docstring for github_event"""
    def __init__(self, payload):
        self.payload = payload

    def execute_event(self):
        print "Nothing to be done here.\r\n"


class pull_event(github_event):
    """docstring for pull_event"""
    def __init__(self, payload):
        super(pull_event, self).__init__(payload)

    def parse_payload():
        pass

    def execute_event():
        self.parse_payload()


class push_event(github_event):
    """docstring for push_event"""
    def __init__(self, payload):
        super(push_event, self).__init__(payload)
        # self.payload = payload

    def parse_event_payload(self):
        self.ref = payload['ref']
        self.commits_size = payload['size']

        # Each commit contains sha, message, author[name, email], url
        self.commits = payload['commits']

    def execute_event(self):
        self.parse_event_payload()

        print self.head
        print self.ref
        print self.size

        for commit in commits:
            print commit['sha'], commit['message'],
            commit['author']['name'], commit['author']['email'], "\n"


class ping_event(github_event):
    """docstring for ping_event"""
    def __init__(self, payload):
        super(ping_event, self).__init__(payload)
        # self.payload = payload

    def parse_event_payload(self):
        self.zen = payload['zen']
        self.hook_id = payload['hook_id']

    def execute_event(self):
        self.parse_event_payload()

        print self.hook_id, self.zen, "\n"


class empty_event(github_event):
    """docstring for empty_event"""
    def __init__(self, event_name, payload):
        self.event_name = event_name
        super(empty_event, self).__init__(payload)

    def parse_event_payload(self):
        # nothing to be done here
        pass

    def execute_event(self):
        self.parse_event_payload()

        print "No handler is implemented for event %r\n" % self.event_name
        print "Payload: "
        pprint.pprint(payload)


def process_event_name(event_name, payload):
    # Construct event handler based on event name
    # Return empty event handler if no proper handler
    # is found
    if event_name == 'push':
        return push_event(payload)
    elif event_name == 'ping':
        return ping_event(payload)
    else:
        return empty_event(event_name, payload)


print "Begin..<br/><br/>\r"
print

initliaze_logging()

form = cgi.FieldStorage()
pprint.pprint(form)

logger.debug(form.getvalue('payload'))

json_payload = form.getvalue('payload', -1)

if json_payload is not -1:
    payload = json.loads(json_payload)
    logger.debug(payload)

    event_handler = process_event_name(
        os.environ['HTTP_X_GITHUB_EVENT'], payload)
    event_handler.execute_event()
else:
    print "<br/>\r"
    print "No payload was receieved!"

    # print " Dumping the recieved values<br/>\r"
    # for key in form:
    #     print "Key %r - Value %r<br/>\r" % (key, form.getvalue(key))
    #     print

print "<br/>End..<br/>\r"
print


# # Get the project name from the query string
# query_string = parse_qs(os.environ['QUERY_STRING'])
# print query_string

# script_dir = os.path.join(os.curdir, 'scripts')
# repo = payload['repository']['name']
# branch = payload['ref'].split('/')[2]

# possible_scripts = [
#     os.path.join(script_dir, repo),
#     os.path.join(script_dir, '%s-%s' % (repo, branch)),
#     os.path.join(script_dir, "all"),
#     ]

# # Run all scripts that exist for either repo, repo-branch, or all
# for script in possible_scripts:
#     if os.path.exists(script):
#         os.system("%s \'%s\'" % (script, json_payload))
#
