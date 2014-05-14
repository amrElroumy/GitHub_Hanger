#!C:/Python27/python.exe -u
# -*- coding: UTF-8 -*-

print "Content-Type: text/html"
print

import cgitb
# Log errors to file
# cgitb.enable(display=0, logdir="/cgi-bin/GitHub_Hanger")
cgitb.enable()

import os
import cgi
import json
import pprint
import logging

logger = logging.getLogger(__name__)
logging_level = logging.DEBUG


def initliaze_logging():
    handler = logging.FileHandler('logfile.log')
    handler.setLevel(logging_level)

    formatter = logging.Formatter(
        '[%(asctime)s] %(filename)s:%(lineno)d - \
        %(levelname)s - %(message)s', '%H:%M:%S')
    handler.setFormatter(formatter)

    logger.setLevel(logging_level)
    logger.addHandler(handler)


class PrettyLog():
    def __init__(self, obj):
        self.obj = obj
    def __repr__(self):
        return pprint.pformat(self.obj)


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

    def parse_event_payload(self):
        self.ref = payload['ref']

        # Each commit contains sha, message, author[name, email], url
        self.commits = payload['commits']

    def execute_event(self):
        self.parse_event_payload()

        print self.ref

        for commit in self.commits:
            print commit['id'], commit['message'],
            commit['author']['name'], commit['author']['email'], "\n"


class ping_event(github_event):
    """docstring for ping_event"""
    def __init__(self, payload):
        super(ping_event, self).__init__(payload)

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


print

initliaze_logging()

logger.info("Beginning Hanger")

form = cgi.FieldStorage()
pprint.pprint(form)

json_payload = form.getvalue('payload', -1)

if json_payload is not -1:
    payload = json.loads(json_payload)
    logger.debug(PrettyLog(payload))

    event_handler = process_event_name(
        os.environ['HTTP_X_GITHUB_EVENT'], payload)
    event_handler.execute_event()
else:
    print "<br/>\r"
    print "No json payload was receieved!<br/>\r"
    logger.error(form)

logger.info("Kan 3ndk hook w ra7 :D")
print
