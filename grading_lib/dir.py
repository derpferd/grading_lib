import os
import hashlib
import shutil
import subprocess


def hash_file(filepath):
    BUF_SIZE = 65536
    sha512 = hashlib.sha512()
    with open(filepath, 'rb') as f:
        while True:
            buf = f.read(BUF_SIZE)
            if not buf:
                break
            sha512.update(buf)

    return sha512.hexdigest()


def get_hashes_for_dir(dirpath, recurive=False):
    hashes = {}

    if recurive:
        for root, dirs, files in os.walk(dirpath):
            for fn in files:
                hashes[fn] = hash_file(os.path.join(root, fn))
    else:
        files = list(map(lambda x: os.path.join(dirpath, x), os.listdir(dirpath)))
        for fn in files:
            hashes[os.path.basename(fn)] = hash_file(fn)

    return hashes


def check_if_dir_contains_files(basedir, otherdir, match_file_names=False):
    org_hashes = get_hashes_for_dir(basedir)
    other_hashes = get_hashes_for_dir(otherdir, recurive=True)
    
    if match_file_names:
        # TODO: write this
        pass
    else:
        for h in org_hashes.values():
            if h not in other_hashes.values():
                return False
    return True


def hard_remove_dir(path):
    path = os.path.abspath(path)
    if os.path.exists(path):
        assert os.path.isdir(path), "Path must be a directory"
        try:
            shutil.rmtree(path)
        except:
            subprocess.check_output(["sudo", "rm", "-rf", path], stderr=subprocess.STDOUT)
