from services.bash.handler import BashHandler

def run(bash: BashHandler, executable: str, args: list) -> int:
    for arg in args:
        if arg == '--help':
            bash.stdout(info['help_long'])
            return 0
        elif arg == '--version':
            bash.stdout(info['version'])
            return 0
        elif arg[0] == '-':
            bash.stderr(f'''whoami: invalid option -- '{arg}'
Try 'whoami --help' for more information.'''.encode('utf-8'))
            return 1
        else:
            bash.stderr(f'''whoami: extra operand ‘{arg}’
Try 'whoami --help' for more information.'''.encode('utf-8'))
            return 1
    bash.stdout(bash.get_user().encode('utf-8'))
    return 0


info = {
    'command': 'whoami',
    'path': ['/usr/bin/whoami', '/bin/whoami'],
    'help_long': b'''Usage: whoami [OPTION]...
Print the user name associated with the current effective user ID.
Same as id -un.

      --help     display this help and exit
      --version  output version information and exit

GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
Report whoami translation bugs to <https://translationproject.org/team/>
Full documentation at: <https://www.gnu.org/software/coreutils/whoami>
or available locally via: info '(coreutils) whoami invocation\'''',
    'help_short': '',
    'version': b'''whoami (GNU coreutils) 8.30
Copyright (C) 2018 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Written by Richard Mlynarik.''',
    'run': run
}