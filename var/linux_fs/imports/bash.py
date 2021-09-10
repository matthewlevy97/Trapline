from services.bash.handler import BashHandler

def run(bash: BashHandler, executable: str, args: list) -> int:
    rebuilt_line = ' '.join(args) + '\n'
    _, _, exit_code = bash.handle_lines([rebuilt_line.encode('utf-8')])
    return exit_code

info = {
    'command': 'bash',
    'path': ['/usr/bin/bash', '/bin/busybox'],
    'help_long': '',
    'help_short': '',
    'run': run
}