"""
This module provides a wrapper to Git.
"""
import os
import sys
import subprocess

from git import Repo
from git.exc import GitCommandError

from collections import namedtuple

git = os.environ.get("GIT_PYTHON_GIT_EXECUTABLE", 'git')
Branch = namedtuple('Branch', ['name', 'is_published'])


class Gitter(object):
    """docstring for Gitter"""
    def __init__(self, repo_dir_path):
        super(Gitter, self).__init__()
        self.dir_path = repo_dir_path

    def repo_check(require_remote=False):
        """Checks that the repo is valid for operation"""
        if self.repo is None:
            print 'Not a git repository.'
            sys.exit(128)

        if not self.repo.remotes and require_remote:
            print 'No git remotes configured. Please add one.'
            sys.exit(128)

        # TODO: You're in a merge state.

    def get_repo():
        """Returns the current Repo, based on path."""

        work_path = subprocess.Popen(
            [git, 'rev-parse', '--show-toplevel'],
            stdout=subprocess.PIPE,
            cwd=os.path.dirname(self.dir_path),
            stderr=subprocess.PIPE).communicate()[0].rstrip('\n')

        if work_path:
            return Repo(work_path)
        else:
            return None


repo = get_repo()
remote = get_remote()
