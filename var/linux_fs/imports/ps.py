from services.bash.handler import BashHandler

def run(bash: BashHandler, executable: str, args: list) -> int:
    output = 'PID   USER     TIME   COMMAND\n'
    for proc in bash.processes():
        output += proc + '\n'
    bash.stdout(output.encode('utf-8'))
    return 0

info = {
    'command': 'ps',
    'path': ['/usr/bin/ps', '/bin/ps'],
    'help_long': '',
    'help_short': '',
    'run': run
}