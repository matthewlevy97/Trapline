from services.bash.handler import BashHandler

def run(bash: BashHandler, executable: str, args: list) -> int:
    return 0

info = {
    'command': '',
    'path': '',
    'help_long': '',
    'help_short': '',
    'run': run
}