import git
import os
import sys

assert sys.version_info.major >= 3 and sys.version_info.minor >= 2, "Python >= 3.2 required"


class GitRepo(object):
    def __init__(self, name, remote_url, cache_dir="."):
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
                if git.Remote(self._repo, "origin") not in self._repo.remotes:
                    self._repo.create_remote("origin", self.remote_url)
            else:
                parent_dir = os.path.dirname(self.path)
                if not os.path.exists(parent_dir):
                    os.makedirs(parent_dir, exist_ok=True)
                self._repo = git.Repo.init(self.path)
                self._repo.create_remote("origin", self.remote_url)
        return self._repo

    def pull(self, branch="master"):
        assert git.Remote(self.repo, "origin") in self.repo.remotes

        origin = self.repo.remotes["origin"]
        origin.pull(branch)

