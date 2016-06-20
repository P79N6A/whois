import subprocess
import shlex
import os
import platform
import re


class Resolver:
    '''
    '''
    def __init__(self):
        pass

    def get_raw_whois(self, domain, program=None):
        timeout = 10

        if not program:
            current_os = platform.system()
            if current_os == 'Linux':
                program = os.path.abspath(
                    path=os.path.join(
                        os.path.dirname(__file__),
                        'bin/whois_elf32',
                    )
                )
            elif current_os == 'Windows':
                program = os.path.abspath(
                    path=os.path.join(
                        os.path.dirname(__file__),
                        'bin/whois.exe',
                    )
                )
            else:
                program = 'whois'

        command = '{program} {domain}'.format(
            program=program,
            domain=domain,
        )
        is_posix = os.name == 'posix'

        completed_process = None
        try:
            completed_process = subprocess.run(
                args=shlex.split(command, posix=is_posix),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exception:
            output = exception.output

        if completed_process:
            output = completed_process.stdout

        whois_raw_data = output.decode('utf-8', errors='ignore')

        process_timed_out = completed_process is None
        process_error = process_timed_out or (completed_process and completed_process.returncode == 0)

        return {
            'whois_data': whois_raw_data,
            'timed_out': process_timed_out,
            'error': process_error,
        }

    def remove_program_banner(self, whois_data):
        '''
        '''
        whois_data = re.sub(
            pattern='.*Mark Russinovich',
            repl='',
            string=whois_data,
            flags=re.DOTALL,
        )
        whois_data = re.sub(
            pattern='^Connecting to.*\.\.\.$',
            repl='',
            string=whois_data,
            flags=re.MULTILINE,
        )

        return whois_data

    def normalize_raw_whois(self, whois_data):
        '''
        '''
        normalized_whois = whois_data

        normalized_whois = normalized_whois.replace('\r\n', '\n')
        normalized_whois = self.remove_program_banner(normalized_whois)
        normalized_whois = normalized_whois.strip()

        return normalized_whois

    def resolve(self, domain):
        '''
        '''
        raw_whois = self.get_raw_whois(
            domain=domain,
        )

        normalized_whois = self.normalize_raw_whois(
            whois_data=raw_whois['whois_data'],
        )
        raw_whois['whois_data'] = normalized_whois

        return raw_whois