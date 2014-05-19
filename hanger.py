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
import urllib
from github import Github
from configobj import ConfigObj


def initliaze_logging(log_file_path, log_format):
    logger = logging.getLogger(__name__)
    logging_level = logging.DEBUG

    handler = logging.FileHandler(log_file_path)
    handler.setLevel(logging_level)

    formatter = logging.Formatter(log_format)

    handler.setFormatter(formatter)

    logger.setLevel(logging_level)
    logger.addHandler(handler)

    return logger


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


class pull_request_event(github_event):
    """docstring for pull_request_event"""
    def __init__(self, payload):
        super(pull_request_event, self).__init__(payload)

    def parse_payload(self):
        # Used for directly accesing the repo
        self.repo_id = self.payload['repository']['id']

        # Used for user-friendly logging
        self.repo_name = self.payload['repository']['name']

        self.pr_number = self.payload['pull_request']['number']

        # Used to mark the last commit that we reviewed
        self.branch_head = self.payload['pull_request']['head']['sha']

        # Store the action type (Open, Syncrhonize, Clos)
        self.action = self.payload['action']

    def _process_files(self, filenames, raw_urls):
        # try:
        import tempfile

        tmp_dir = tempfile.mkdtemp()

        with open(tmp_dir + "\\" + 'pathLookup.meta', 'w') as path_lookup_file:
            for fname, furl in zip(filenames, raw_urls):
                # request file and save it locally
                urllib.urlretrieve(
                    furl, tmp_dir + "\\" + os.path.basename(fname))

                # map the relative path and the name of the file
                path_lookup_file.write(
                    os.path.basename(fname) + " :- " + fname + "\n")

        # finally:
        #     try:
        #         import shutil

        #         shutil.rmtree(tmp_dir, ignore_errors=True)
        #     except OSError as exc:
        #         if exc.errno != errno.ENOENT:
        #             logger.error("%r - %r"%(exc.errno, exc.strerror))

    def execute_event(self):
        self.parse_payload()

        gh = Github(GITHUB_AUTHENTICATION_TOKEN)

        # Get Commits' IDs
        repo = gh.get_repo(self.repo_id)
        pull_request = repo.get_pull(self.pr_number)
        commits = pull_request.get_commits()

        all_file_names = []
        all_raw_urls = []

        # Get modified files throughout the pull request commits
        # foreach commit (from last to first):
        # get modified files, if file was checked before
        # don't get it in current commit
        for commit in commits.reversed:
            commit_modified_files = commit.files

            new_modified_filenames = []
            new_modified_urls = []

            for f in commit_modified_files:
                if f.filename not in all_file_names:
                    new_modified_filenames.append(f.filename)
                    new_modified_urls.append(f.raw_url)

            all_file_names = all_file_names + new_modified_filenames
            all_raw_urls = all_raw_urls + new_modified_urls

        self._process_files(all_file_names, all_raw_urls)


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
    elif event_name == 'pull_request':
        return pull_request_event(payload)
    else:
        return empty_event(event_name, payload)


print


CONFIG_PATH = "config.ini"

config = ConfigObj(CONFIG_PATH, create_empty=True)

GITHUB_AUTHENTICATION_TOKEN = config['GitHub']['API_TOKEN']
LOG_FILE_PATH = config['Logging']['LOG_PATH']
log_format = config['Logging']['Format']

logger = initliaze_logging(LOG_FILE_PATH, log_format)

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
