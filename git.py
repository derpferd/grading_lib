import git
import os
import sys
import subprocess

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

    def diff(self, start, end=None, color=False):
        if color:
            if end:
                return self.repo.git.execute(["git", "-c", "color.ui=always", "diff", start.hexsha, end.hexsha])
            else:
                return self.repo.git.execute(["git", "-c", "color.ui=always", "diff", start.hexsha])
        else:
            if end:
                return self.repo.git.diff(start, end)
            else:
                return self.repo.git.diff(start)

    def html_diff(self, start, end=None):
        if end:
            diff = self.repo.git.diff(start, end)
        else:
            diff = self.repo.git.diff(start)
        return "<pre><code>{}</code></pre>".format(diff)
        # out = subprocess.check_output(["pygmentize", "-f", "html", "-O", "style=emacs", "-l", "diff"], input=diff.encode(encoding="utf-8")).decode(encoding="utf-8")
        # return "<div class='diff'>{}</div>".format(out)

    def commit(self, *args):
        return self.repo.commit(*args)

    def pull(self, branch="master"):
        assert git.Remote(self.repo, "origin") in self.repo.remotes

        origin = self.repo.remotes["origin"]
        origin.pull(branch)


def list_committed_file_after_commit(repo, commit):
    cur_commit = repo.active_branch.commit

    files = []
    for diff in cur_commit.diff(commit):
        files += [diff.a_path]

    return files
