import subprocess
import shlex
import os
import re
import select
import time

from . import _resolver


class Resolver(
    _resolver.Resolver,
):
    name = 'program'

    @classmethod
    def get_raw_whois(
        cls,
        domain,
        whois_binary_path='whois',
    ):
        if whois_binary_path is None:
            whois_binary_path_result = Resolver.find_executable(
                executable_name='whois',
            )
            if whois_binary_path_result:
                whois_binary_path = whois_binary_path_result

        command = '{program} {domain}'.format(
            program=whois_binary_path,
            domain=domain,
        )
        is_posix = os.name == 'posix'

        raw_whois = cls.get_command_output(
            command=command,
            is_posix=is_posix,
            timeout=10,
        )

        return raw_whois

    @classmethod
    def get_command_output(
        cls,
        command,
        is_posix,
        timeout=10,
    ):
        process = None
        all_output = ''
        start_time = time.time()

        try:
            poller = select.epoll()

            process = subprocess.Popen(
                args=shlex.split(
                    s=command,
                    posix=is_posix,
                ),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            poller.register(process.stdout, select.EPOLLHUP | select.EPOLLIN)

            while start_time + timeout > time.time():
                for fileno, event in poller.poll(
                    timeout=1,
                ):
                    if event & select.EPOLLHUP:
                        poller.unregister(
                            fd=fileno,
                        )

                        break

                    output = process.stdout.read()
                    output = output.decode(
                        encoding='utf-8',
                        errors='ignore',
                    )
                    all_output += output

                try:
                    process.wait(0)

                    break
                except subprocess.TimeoutExpired:
                    pass
        finally:
            if process is not None:
                process.terminate()

                try:
                    os.waitpid(
                        process.pid,
                        0,
                    )
                except ChildProcessError:
                    pass

                output = process.stdout.read()
                output = output.decode(
                    encoding='utf-8',
                    errors='ignore',
                )
                all_output += output

                try:
                    process.kill()
                except ProcessLookupError:
                    pass

        empty_whois_result = all_output.strip() == ''
        timedout_whois_result = 'Interrupted by signal 15...' in all_output

        if empty_whois_result or timedout_whois_result:
            raise _resolver.WhoisTimedOut()
        else:
            return all_output.strip()

    @classmethod
    def remove_program_banner(
        cls,
        raw_whois,
    ):
        raw_whois = re.sub(
            pattern=r'.*Mark Russinovich',
            repl='',
            string=raw_whois,
            flags=re.DOTALL,
        )
        raw_whois = re.sub(
            pattern=r'^Connecting to.*\.\.\.$',
            repl='',
            string=raw_whois,
            flags=re.MULTILINE,
        )

        return raw_whois

    @classmethod
    def normalize_raw_whois(
        cls,
        raw_whois,
    ):
        normalized_whois = raw_whois

        normalized_whois = normalized_whois.replace('\r\n', '\n')
        normalized_whois = cls.remove_program_banner(normalized_whois)
        normalized_whois = normalized_whois.strip()

        return normalized_whois

    @staticmethod
    def find_executable(
        executable_name,
    ):
        paths = os.environ['PATH'].split(os.pathsep)
        for path in paths:
            executable_path = os.path.join(path, executable_name)
            if os.path.isfile(
                path=executable_path,
            ):
                return executable_path

        return None
