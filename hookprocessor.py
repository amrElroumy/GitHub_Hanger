#!/usr/bin/env python

import os
import logging
import subprocess

from json import loads
from pprint import pformat
from urllib import urlretrieve
from configobj import ConfigObj
from sys import argv, exc_info, executable
from github import Github, GithubException


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
        return pformat(self.obj)


class LintWrapper(object):
    """docstring for LintWrapper"""
    @staticmethod
    def lint_files(working_dir, command):
        logger.debug('Starting linting.')

        logger.debug(command)
        logger.debug(working_dir)

        try:
            p = subprocess.Popen(
                [executable, command, working_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)

            logger.debug(p.communicate())

        except subprocess.CalledProcessError as e:
            logger.debug(e.returncode)
            logger.debug(p.communicate())
            return None

        logger.debug('Finished linting.')
        return "flintOutput"

    @staticmethod
    def parse_lints(lint_output_path, delimiter):
        logger.info('Parsing lints.')

        bulk_lints = ''
        with open(lint_output_path, 'r') as lints:
            bulk_lints = lints.read()

            bulk_lints = bulk_lints.strip(delimiter).split(delimiter)

        # Combine the each parsed lint into a tuple to easy processing
        lints = zip(bulk_lints[0::3], bulk_lints[1::3], bulk_lints[2::3])

        logger.info('Finished parsing lints.')
        return lints


class GithubWrapper(object):
    """docstring for GithubWrapper"""
    @staticmethod
    def download_commit_files(working_dir, filenames, raw_urls):
        logger.debug('Downloading the commit files.')

        path = working_dir + "/" + 'pathLookup.meta'
        with open(path, 'w') as path_lookup_file:
            for fname, furl in zip(filenames, raw_urls):
                # request file and save it locally
                urlretrieve(furl, working_dir + "/" + os.path.basename(fname))

                # map the relative path and the name of the file
                path_lookup_file.write(
                    os.path.basename(fname) + " :- " + fname + "\n")

        logger.debug('Finished downloading the commit files.')

    @staticmethod
    def post_review_comments(pull_request, filenames, lints):
        logger.info('Posting review comments.')

        head_commit = pull_request.get_commits().reversed[0]

        path_lookup = {os.path.basename(p): p for p in filenames}

        for path, position, comment_body in lints:

            basename = os.path.basename(path)
            comment_body = position + ': ' + comment_body
            comment_body = comment_body.strip("\n")

            filepath = path_lookup[basename]

            pull_request.create_review_comment(
                comment_body,
                head_commit,
                filepath, 0)

        logger.info('Finished posting review comments.')


class GithubEvent(object):
    """docstring for GithubEvent"""
    def __init__(self, payload):
        self.payload = payload

    @staticmethod
    def event_factory(event_name, payload):
        # Construct event handler based on event name
        # Return empty event handler if no proper handler is found
        if event_name == 'push':
            return PushEvent(payload)
        elif event_name == 'ping':
            return PingEvent(payload)
        elif event_name == 'pull_request':
            return PullRequestEvent(payload)
        else:
            return EmptyEvent(event_name, payload)

    def execute_event(self):
        logger.debug("Nothing to be done here.\r\n")


class PullRequestEvent(GithubEvent):
    """docstring for PullRequestEvent"""
    def __init__(self, payload):
        super(PullRequestEvent, self).__init__(payload)
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
        import tempfile
        working_dir = tempfile.mkdtemp(dir=PVT_DIR_PATH)

        GithubWrapper.download_commit_files(
            working_dir, all_file_names, all_raw_urls)

        lint_output_path = LintWrapper.lint_files(working_dir, FLINT_COMMAND)

        if lint_output_path is not None:
            lints = LintWrapper.parse_lints(
                working_dir + "/" + lint_output_path, DELIMITER_TOKEN)

            if lints:
                GithubWrapper.post_review_comments(
                    self.pull_request, all_file_names, lints)

        try:
            import shutil

            shutil.rmtree(working_dir, ignore_errors=True)
        except OSError as exc:
            logger.error("%r - %r" % (exc.errno, exc.strerror))


class PushEvent(GithubEvent):
    """docstring for PushEvent"""
    def __init__(self, payload):
        super(PushEvent, self).__init__(payload)

    def parse_event_payload(self):
        self.ref = self.payload['ref']

        # Each commit contains sha, message, author[name, email], url
        self.commits = self.payload['commits']

    def execute_event(self):
        self.parse_event_payload()

        logger.debug(self.ref)

        for commit in self.commits:
            logger.debug(
                commit['id'], commit['message'],
                commit['author']['name'], commit['author']['email'], "\n")


class PingEvent(GithubEvent):
    """docstring for PingEvent"""
    def __init__(self, payload):
        super(PingEvent, self).__init__(payload)

    def parse_event_payload(self):
        self.zen = payload['zen']
        self.hook_id = payload['hook_id']

    def execute_event(self):
        self.parse_event_payload()

        logger.debug(self.hook_id, self.zen, "\n")


class EmptyEvent(GithubEvent):
    """docstring for EmptyEvent"""
    def __init__(self, event_name, payload):
        self.event_name = event_name
        super(EmptyEvent, self).__init__(payload)

    def parse_event_payload(self):
        # nothing to be done here
        pass

    def execute_event(self):
        self.parse_event_payload()

        logger.debug('No handler implemented for event %s' % self.event_name)
        logger.debug('Payload: ')
        logger.debug(PrettyLog(payload))


## Loading configurations
CONFIG_PATH = "/var/www/ghservice/config.ini"

config = ConfigObj(CONFIG_PATH, interpolation=False)

GITHUB_AUTHENTICATION_TOKEN = config['GitHub']['API_TOKEN']
LOG_FILE_PATH = config['Logging']['LOG_PATH']
LOG_FORMAT = config['Logging']['LOG_FORMAT']
LOG_DATE_FORMAT = config['Logging']['DATE_FORMAT']

FLINT_COMMAND = config['Linters']['FLINT']
DELIMITER_TOKEN = config['Linters']['DELIMITER_TOKEN']

PVT_DIR_PATH = config['Application']['PVT_DIR']
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
    json_payload = loads(payload)
os.remove(payload_path)

event_handler = GithubEvent.event_factory(event_name, json_payload)

try:
    logger.info('Beginning event execution.')
    event_handler.execute_event()
    logger.info('Finished event execute_event.')

except GithubException as e:
    logger.error(e.status + " - " + e.data)
    raise

except:
    logger.error("Unexpected error:", exc_info()[0])
    raise

logger.info("Finished hook processing")
