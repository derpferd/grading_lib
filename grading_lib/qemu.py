#!/usr/bin/python3
import os
import re
import subprocess
import time
import socket
from random import randint
from threading import Lock, Thread
from queue import Queue
from subprocess import DEVNULL


class XV6Output:
    def __init__(self, out):
        self.out = out

    def __str__(self):
        # TODO: write this
        pass


class XV6CompileError(XV6Output):
    pass


class XV6KernelPanic(XV6Output):
    pass


class XV6ConnectionResetError(XV6Output):
    pass


class XV6Runner(object):
    VERBOSE = False

    def __init__(self, working_dir, cpus=2, mem=512):
        """
        args:
            working_dir: the place where xv6 is.
            inputs: a list of strs to pass to the os when it boots
        """
        self.working_dir = working_dir
        self.cpus = cpus
        self.mem = mem

    def run(self, inputs, raw_mode=False, timeout=30.0):
        """
        Args:
             inputs(Iterable of bytes): this is an array containing bytes of the commands to run.
             raw_mode(bool): raw_mode returns all output by the system instead of parsing it into different
                             outputs for each command.
        """
        inputs = list(inputs)  # Make sure that inputs is an iterable.
        assert set(map(lambda x: isinstance(x, bytes), inputs + [b''])) == {True}, "All inputs must be of type bytes."

        def get_cmd_out(channel, cmd=None):
            channel.settimeout(timeout)
            time.sleep(0.01)
            if cmd is not None:
                channel.send(cmd)
            out = b''
            while b'$' not in out and b'panic' not in out:
                time.sleep(0.01)
                try:
                    out += channel.recv(1024)
                except ConnectionResetError:
                    return None

            if cmd is not None:
                cmd_loc = out.find(cmd)
                out = out[cmd_loc + len(cmd):]

            # find the last $
            last_dollar_sign_pos = len(out)-(out[::-1].find(b'$')+1)
            out = out[:last_dollar_sign_pos]
            return out

        def get_raw_out(channel, cmd=None, timeout=2):
            """
            Args:
                timeout(bool): How long to wait for new input.
            """
            channel.settimeout(timeout)
            if cmd is not None:
                channel.send(cmd)
            out = b''
            while True:
                new_out = b''
                try:
                    new_out = channel.recv(1024)
                except socket.timeout:
                    pass
                if self.VERBOSE:
                    print("Got out! '{}'".format(new_out))
                out += new_out
                if not new_out:
                    break

            return out

        def shell_worker(ready_lock, queue, commands, raw_mode):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            port = 4000 + randint(0, 999)  # This is to make the probably to getting multiple Address in Use errors lower.
            bound = False
            while not bound:
                port += 1
                try:
                    sock.bind(("127.0.0.1", port))
                    bound = True
                except OSError as e:
                    print("Had error: {}".format(e))
            sock.listen(1)  # Only allow one connection
            queue.put(port)

            if self.VERBOSE:
                print("Shell worker port: {}".format(port))

            ready_lock.release()
            (channel, addr) = sock.accept()

            if raw_mode:
                raw_out = get_raw_out(channel)
                for cmd in commands:
                    raw_out += get_raw_out(channel, cmd=cmd)
                queue.put(raw_out)
            else:
                intro = get_cmd_out(channel)
                for cmd in commands:
                    if cmd[-1] != b"\n":
                        if self.VERBOSE:
                            print("Warning: Adding newline to command!")
                        cmd = cmd + b"\n"
                    cmd_out = get_cmd_out(channel, cmd=cmd)
                    queue.put(cmd_out)

            # print("Shell out", intro)
            # print("Shell out", ls_out)

            sock.close()

        if self.VERBOSE:
            print("Building xv6...")
        # Build xv6
        # subprocess.check_output(["make", "clean"], cwd="test")
        try:
            subprocess.check_output(["make"], cwd=self.working_dir, stderr=subprocess.STDOUT)
        except:
            print("Something went wrong compiling xv6. :(")
            return None

        shell_ready_lock = Lock()
        shell_ready_lock.acquire()

        queue = Queue()

        shell_thread = Thread(target=shell_worker, args=(shell_ready_lock, queue, inputs, raw_mode))
        shell_thread.start()
        # cmd_thread = Thread(target=cmd_worker, args=(cmd_ready_lock, kill_lock, queue))
        # cmd_thread.start()

        shell_ready_lock.acquire()
        # cmd_ready_lock.acquire()

        shell_port = queue.get()

        # for _ in range(2):
        #
        #     if name == "cmd":
        #         cmd_loc_num = val
        #     if name == "shell":
        #         shell_loc_num = val

        # if shell_loc_num == cmd_loc_num:
        #     return None

        if self.VERBOSE:
            print("Ready to rock and roll!")
            print("Now wiring up the machine :P")
            print("Config: shell_loc_num: {}".format(shell_port))
        qemu_ps = subprocess.Popen(["qemu-system-i386", "-drive", "file=fs.img,index=1,media=disk,format=raw", "-drive", "file=xv6.img,index=0,media=disk,format=raw", "-smp", str(self.cpus), "-m", str(self.mem), "-nographic", "-chardev", "socket,host=127.0.0.1,port={},id=gnc0".format(shell_port), "-device", "isa-serial,chardev=gnc0", "-monitor", "stdio", "-smp", str(self.cpus), "-m", str(self.mem)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=DEVNULL, cwd=self.working_dir)

        shell_thread.join(timeout=timeout)
        output = None
        if not shell_thread.is_alive():
            if raw_mode:
                output = queue.get(block=False)
            else:
                output = []
                for _ in inputs:
                    output += [queue.get(block=False)]
        # else:
        #     shell_thread.

        qemu_ps.stdin.write(bytearray("quit\n", encoding="utf-8"))
        if self.VERBOSE:
            print("Poll: {}".format(qemu_ps.poll()))
        qemu_ps.kill()
        return output


def main():
    out = XV6Runner("/home/derpferd/Documents/umd ta/3_S18/os/grading/lab2/input/gordo488/lab2/part2").run([b"date"])
    print("Out: {}".format(out))


if __name__ == '__main__':
    main()
