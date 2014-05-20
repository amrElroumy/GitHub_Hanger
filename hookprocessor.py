import os
import json
import pprint
import logging
import subprocess

from sys import argv
from github import Github
from sys import executable
from urllib import urlretrieve
from configobj import ConfigObj

import cgitb
cgitb.enable()


def initialize_logging(log_file_path, logfmt, datefmt):
    logger = logging.getLogger(__name__)
    logging_level = 10

    handler = logging.FileHandler(log_file_path)
    handler.setLevel(logging_level)

    formatter = logging.Formatter(logfmt, datefmt)

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
        print("Nothing to be done here.\r\n")


class pull_request_event(github_event):
    """docstring for pull_request_event"""
    def __init__(self, payload):
        super(pull_request_event, self).__init__(payload)
        logger.debug('Initialized "pull request" event handler')

    def parse_payload(self):
        logger.debug('Parsing payload')

        # Used for directly accessing the repo
        self.repo_id = self.payload['repository']['id']

        # Used for user-friendly logging
        self.repo_name = self.payload['repository']['name']

        self.pr_number = self.payload['pull_request']['number']

        # Used to mark the last commit that we reviewed
        self.branch_head = self.payload['pull_request']['head']['sha']

        # Store the action type (Open, Synchronize, Close)
        self.action = self.payload['action']

        logger.debug('Finished parsing payload')

    def _download_commit_files(self, working_dir, filenames, raw_urls):
        logger.debug('Downloading the commit files.')

        path = working_dir + "\\" + 'pathLookup.meta'
        with open(path, 'w') as path_lookup_file:
            for fname, furl in zip(filenames, raw_urls):
                # request file and save it locally
                urlretrieve(furl, working_dir + "\\" + os.path.basename(fname))

                # map the relative path and the name of the file
                path_lookup_file.write(
                    os.path.basename(fname) + " :- " + fname + "\n")

        logger.debug('Finished downloading the commit files.')

    def _lint_files(self, working_dir, command):
        logger.debug('Starting linting.')

        p = subprocess.Popen(
            [executable, command, working_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE)
        p.communicate()

        logger.debug('Finished linting.')
        return "flintOutput"

    def _parse_lints(self, lint_output_path, delimiter):

        logger.debug('Parsing lints.')

        bulk_lints = ''
        with open(lint_output_path, 'r') as lints:
            bulk_lints = lints.read()

            bulk_lints = bulk_lints.strip(delimiter).split(delimiter)

        lints = zip(bulk_lints[0::3], bulk_lints[1::3], bulk_lints[2::3])

        for lint in lints:
            logger.debug(lint)

        logger.debug('Finished parsing lints.')

        return lints

    def _post_review_comments(self, filenames, lints):
        logger.debug('Posting review comments.')

        head_commit = self.pull_request.get_commits().reversed[0]

        path_lookup = [(os.path.basename(p), p) for p in filenames]

        for path, position, comment_body in lints:

            basename = os.path.basename(path)
            comment_body = position + ': ' + comment_body

            filepath = path_lookup[basename] + '/' + os.path.basename(basename)
            self.pull_request.create_review_comment(
                comment_body, head_commit, filepath, 0)

        logger.debug('Finished posting review comments.')

    def execute_event(self):
        self.parse_payload()

        gh = Github(GITHUB_AUTHENTICATION_TOKEN)

        # Get Commits' IDs
        repo = gh.get_repo(self.repo_id)
        self.pull_request = repo.get_pull(self.pr_number)
        commits = self.pull_request.get_commits()

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

        # Create tmp directory for processing
        # try:
        import tempfile
        working_dir = tempfile.mkdtemp()

        self._download_commit_files(working_dir, all_file_names, all_raw_urls)
        lint_output_path = self._lint_files(working_dir, FLINT_COMMAND)
        lints = self._parse_lints(
            working_dir + "\\" + lint_output_path, DELIMITER_TOKEN)
        self._post_review_comments(all_file_names, lints)

        # finally:
        #     try:
        #         import shutil

        #         shutil.rmtree(working_dir, ignore_errors=True)
        #     except OSError as exc:
        #         if exc.errno != errno.ENOENT:
        #             logger.error("%r - %r"%(exc.errno, exc.strerror))


class push_event(github_event):
    """docstring for push_event"""
    def __init__(self, payload):
        super(push_event, self).__init__(payload)

    def parse_event_payload(self):
        self.ref = self.payload['ref']

        # Each commit contains sha, message, author[name, email], url
        self.commits = self.payload['commits']

    def execute_event(self):
        self.parse_event_payload()

        print(self.ref)

        for commit in self.commits:
            print(
                commit['id'], commit['message'],
                commit['author']['name'], commit['author']['email'], "\n")


class ping_event(github_event):
    """docstring for ping_event"""
    def __init__(self, payload):
        super(ping_event, self).__init__(payload)

    def parse_event_payload(self):
        self.zen = payload['zen']
        self.hook_id = payload['hook_id']

    def execute_event(self):
        self.parse_event_payload()

        print(self.hook_id, self.zen, "\n")


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

        print("No handler is implemented for event %r\n" % self.event_name)
        print("Payload: ")
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

## Loading configurations
CONFIG_PATH = "config.ini"

config = ConfigObj(CONFIG_PATH, interpolation=False)

GITHUB_AUTHENTICATION_TOKEN = config['GitHub']['API_TOKEN']
LOG_FILE_PATH = config['Logging']['LOG_PATH']
LOG_FORMAT = config['Logging']['LOG_FORMAT']
LOG_DATE_FORMAT = config['Logging']['DATE_FORMAT']

FLINT_COMMAND = config['Linters']['FLINT']
DELIMITER_TOKEN = config['Linters']['DELIMITER_TOKEN']
## Finished loading configurations

logger = initialize_logging(LOG_FILE_PATH, LOG_FORMAT, LOG_DATE_FORMAT)

## Begin logic
logger.info("Beginning hook processing")

script, payload_path = argv

event_name = ''
json_payload = []

with open(payload_path, 'r') as out:
    event_name = out.readline().strip("\n")
    payload = out.readline()
    json_payload = json.loads(payload)
# os.remove(payload_path)

event_handler = process_event_name(event_name, json_payload)

logger.debug('Beginning event execution.')
event_handler.execute_event()
logger.debug('Finished event execute_event.')

logger.info("Finished hook processing")
