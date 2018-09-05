import os
import shutil
import sys
from typing import Optional, Union, List

import git

assert sys.version_info.major >= 3 and sys.version_info.minor >= 5, "Python >= 3.5 required"


class GitRepo(object):
    def __init__(self, name, remote_url=None, cache_dir="."):
        self.name = name
        self.remote_url = remote_url
        self.cache_dir = cache_dir
        self._repo = None

    @property
    def path(self):
        full_path = os.path.abspath(os.path.join(self.cache_dir, self.name))
        return full_path

    @property
    def is_branchless(self):
        return len(self.repo.branches) == 0

    @property
    def repo(self):
        if not self._repo:
            if os.path.exists(self.path):
                self._repo = git.Repo(self.path)
                if git.Remote(self._repo, "origin") not in self._repo.remotes and self.remote_url:
                    self._repo.create_remote("origin", self.remote_url)
            elif self.remote_url:
                parent_dir = os.path.dirname(self.path)
                if not os.path.exists(parent_dir):
                    os.makedirs(parent_dir, exist_ok=True)
                self._repo = git.Repo.init(self.path)
                self._repo.create_remote("origin", self.remote_url)
            else:
                raise Exception("Couldn't find location repo and no remote was given.")
        return self._repo

    def diff(self, start, end=None, color=False, exclude: Optional[Union[str, List]]=None, include: Optional[Union[str, List]]=None):
        """

        Args:
            start:
            end:
            color:
            exclude: A list or str of path(s) to exclude from diff.
            include: A list or str of path(s) to include to diff.

        Returns:

        """
        extra_args = []
        if include:
            if isinstance(include, str):
                extra_args += [f':{include}']
            elif isinstance(include, list):
                for path in include:
                    extra_args += [f':{path}']

        if exclude:
            if isinstance(exclude, str):
                extra_args += [f':!{exclude}']
            elif isinstance(exclude, list):
                for path in exclude:
                    extra_args += [f':!{path}']

        if color:
            if end:
                diff_unsafe_string = self.repo.git.execute(["git", "-c", "color.ui=always", "diff", start.hexsha, end.hexsha] + extra_args)
            else:
                diff_unsafe_string = self.repo.git.execute(["git", "-c", "color.ui=always", "diff", start.hexsha] + extra_args)
        else:
            if end:
                diff_unsafe_string = self.repo.git.diff(start, end, *extra_args)
            else:
                diff_unsafe_string = self.repo.git.diff(start, *extra_args)
        return diff_unsafe_string.encode("utf-8", "replace").decode("utf-8")

    def html_diff(self, start, end=None, exclude=None, include=None):
        return f"<pre><code>{self.diff(start, end, color=False, exclude=exclude, include=include)}</code></pre>"
        # out = subprocess.check_output(["pygmentize", "-f", "html", "-O", "style=emacs", "-l", "diff"], input=diff.encode(encoding="utf-8")).decode(encoding="utf-8")
        # return "<div class='diff'>{}</div>".format(out)

    def log(self, start, end=None):
        if end:
            log_string = self.repo.git.log(f'{start}...{end}')
        else:
            log_string = self.repo.git.log(f'{start}...')
        return log_string.encode("utf-8", "replace").decode("utf-8")

    def html_log(self, start, end=None):
        return f"<pre><code>{self.log(start, end)}</code></pre>"

    def commit(self, *args):
        return self.repo.commit(*args)

    def pull(self, branch="master"):
        assert git.Remote(self.repo, "origin") in self.repo.remotes

        origin = self.repo.remotes["origin"]
        origin.pull(branch)

    def remove(self):
        self._repo = None
        shutil.rmtree(self.path)


def list_committed_file_after_commit(repo, commit):
    cur_commit = repo.active_branch.commit

    files = []
    for diff in cur_commit.diff(commit):
        files += [diff.a_path]

    return files
