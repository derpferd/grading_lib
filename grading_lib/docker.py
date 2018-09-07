import io
import os
import shutil
import tarfile
import tempfile
from pathlib import Path
from subprocess import CompletedProcess
from typing import Dict, Union

import docker
import requests


class DockerTimeoutException(Exception):
    pass


class DockerGrader:
    CPUS = 2  # Protect against cpu usage attacks
    MAX_DISK = "100m"  # Protect against filling up the disk
    MEMORY_LIMIT = "300m"  # Protect against memory usage attacks
    PIDS_LIMIT = 1000  # Protect against fork-bomb like attacks

    CPU_PERIOD = 100000  # Interval for checking/enforcing cpu usage limits.

    def __init__(self, image: str, cmd: str='bash /wrapper.sh', default_timeout: int=60):
        self.image = image
        self.cmd = cmd
        self.client = docker.from_env()
        self.default_timeout_sec = default_timeout
    
    def run(self, files: Dict[Union[str, Path], Union[str, Path]], timeout: int=None) -> CompletedProcess:
        """
        Args:
            files: A dictionary mapping files pathes on the host to a path on the guest relative to the testing env.
            timeout: The number of seconds to wait for the program to run before killing it.
        Raises:
            DockerTimeoutException: Raised if program don't return before timeout.
        """
        if timeout is None:
            timeout = self.default_timeout_sec

        client = docker.from_env()
        container = client.containers.create(self.image,
                             self.cmd,
                             mem_limit=DockerGrader.MEMORY_LIMIT,
                             pids_limit=DockerGrader.PIDS_LIMIT,
                             cpu_period=DockerGrader.CPU_PERIOD,
                             cpu_quota=int(DockerGrader.CPU_PERIOD * DockerGrader.CPUS),
                             tmpfs={
                                 '/foo': f'size={DockerGrader.MAX_DISK},exec'
                             },
                             detach=True, )

        container.put_archive(path='/tmp', data=self.create_file_bundle(files))
        container.start()

        try:
            results = container.wait(timeout=timeout)
        except requests.exceptions.ReadTimeout:  # They timed out.
            raise DockerTimeoutException

        if results['Error']:
            raise Exception(f'HAD ERROR :{results["Error"]}')

        return CompletedProcess(args=self.cmd,
                                returncode=results['StatusCode'],
                                stdout=container.logs(stdout=True, stderr=False),
                                stderr=container.logs(stdout=False, stderr=True))
        
    def create_file_bundle(self, files: Dict[Union[str, Path], Union[str, Path]]) -> bytes:
        archive = io.BytesIO()

        with tempfile.TemporaryDirectory() as tmpdirname:
            dir_name = os.path.join(tmpdirname, "env_add")
            os.mkdir(dir_name)
            for src, dest in files.items():
                shutil.copy2(src, os.path.join(dir_name, str(dest)))
            with tarfile.open(fileobj=archive, mode="w:gz") as tf:
                tf.add(dir_name, arcname=os.path.basename(dir_name))

        return archive.getvalue()

    @staticmethod
    def build_docker_image(image_name, build_path):
        assert image_name == image_name.lower(), "Image name must be lower case."
        client = docker.from_env()
        client.images.build(path=os.path.abspath(build_path), tag=image_name)
