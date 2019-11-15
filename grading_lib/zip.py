import os
import tarfile
import zipfile
from shutil import copyfile

from grading_lib import Roster


def ensure_dir_exists(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


def extract_zip(zippath, zipdir):
    with zipfile.ZipFile(zippath) as zf:
        zf.extractall(zipdir)


def extract_moodle_zip(zippath, outpath, tmpdir, roster: Roster, internal_tarball=True):
    zipdir = os.path.join(tmpdir, "zip")
    extract_zip(zippath, zipdir)
    ensure_dir_exists(outpath)

    for subdir in os.listdir(zipdir):
        name = subdir.split("_")[0]
        parts = name.split(" ")
        fname, lname = " ".join(parts[:-1]), parts[-1]

        sid = roster.get_student_id_by_name(fname, lname)

        if sid is None:
            continue
        # assert sid is not None, "Unknown student"

        if internal_tarball:
            # TODO: catch exceptions and give good error.
            tarpath = os.path.join(zipdir, subdir)
            if os.path.isdir(tarpath):
                tarball_name = os.listdir(os.path.join(zipdir, subdir))[0]
                tarpath = os.path.join(zipdir, subdir, tarball_name)

#            if not tarpath.endswith(".tar.gz"):
#                print("Student submission must be a tar.gz. filename was {}".format(tarpath))
#                continue
            sopath = os.path.join(outpath, sid)
            try:
                with tarfile.open(tarpath, mode="r:*") as tf:
                    tf.extractall(sopath)
            except tarfile.ReadError:
                print("Submission was not a valid tarball.")
            print(sid)
        else:
            submission_name = os.listdir(os.path.join(zipdir, subdir))[0]
            submissionpath = os.path.join(zipdir, subdir, submission_name)

            ext = ""
            if "." in submission_name:
                ext = submission_name[submission_name.index("."):]
            new_path = os.path.join(outpath, sid + ext)

            copyfile(submissionpath, new_path)


def extract_canvas_zip(zippath, outpath, tmpdir, roster: Roster, internal_tarball=True):
    zipdir = os.path.join(tmpdir, "zip")
    extract_zip(zippath, zipdir)
    ensure_dir_exists(outpath)
    print('honk')
    for file in os.listdir(zipdir):
        zipdir = os.path.join(tmpdir, "zip")
        extract_zip(zippath, zipdir)
        ensure_dir_exists(outpath)

        for subdir in os.listdir(zipdir):
            # ext_id from canvas is listed second if not late, otherwise listed third
            # either fnamelname_extid_whatever or fnamelname_LATE_extid_whatever
            if "LATE" in subdir:
                ext_id = subdir.split("_")[2]
            else:
                ext_id = subdir.split("_")[1]

            sid = roster.get_student_id_by_external_id(ext_id)

            if sid is None:
                continue
            # assert sid is not None, "Unknown student"

            if internal_tarball:
                # TODO: catch exceptions and give good error.
                tarpath = os.path.join(zipdir, subdir)
                if os.path.isdir(tarpath):
                    tarball_name = os.listdir(os.path.join(zipdir, subdir))[0]
                    tarpath = os.path.join(zipdir, subdir, tarball_name)

                #            if not tarpath.endswith(".tar.gz"):
                #                print("Student submission must be a tar.gz. filename was {}".format(tarpath))
                #                continue
                sopath = os.path.join(outpath, sid)
                try:
                    with tarfile.open(tarpath, mode="r:*") as tf:
                        tf.extractall(sopath)
                except:
                    print("Submission was not a valid tarball.")
                print(sid)
            else:
                submission_name = subdir
                submissionpath = os.path.join(zipdir, submission_name)

                ext = ""
                if "." in submission_name:
                    ext = submission_name[submission_name.index("."):]
                new_path = os.path.join(outpath, sid + ext)

                copyfile(submissionpath, new_path)