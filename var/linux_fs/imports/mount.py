from services.bash.handler import BashHandler

def run(bash: BashHandler, executable: str, args: list) -> int:
    vfs = bash.get_vfs()
    bash.stdout(vfs.read_file('/proc/mounts'))
    return 0

info = {
    'command': 'mount',
    'path': ['/usr/bin/mount', '/bin/mount'],
    'help_long': '',
    'help_short': '',
    'run': run
}