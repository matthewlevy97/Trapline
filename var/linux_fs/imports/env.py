from services.bash.handler import BashHandler

def run(bash: BashHandler, executable: str, args: list) -> int:
    line_ending = '\r\n'
    for i in range(len(args)):
        if args[i] == '-0' or args[i] == '--null':
            line_ending = '\0'
        elif args[i].startswith('-u') or args[i].startswith('--unset'):
            split = args[i].split('=', 1)
            if len(split) == 2:
                unsetvar = split[1]
            elif i+1 < len(args):
                i += 1
                unsetvar = split[1]
            else:
                bash.stderr(f'''env: option requires an argument -- '{args[i].replace("-", "")}'
Try 'env --help' for more information.'''.encode('utf-8'))
                return 1
            bash.unset_environment_variable(unsetvar)
        elif args[i] == '--help':
            bash.stdout(info['help_long'].encode('utf-8'))
            return 0
        elif args[i] == '--version':
            bash.stdout(info['version'].encode('utf-8'))
            return 0
        else:
            bash.stderr(f'''env: invalid option -- '{args[i].replace("-", "")}'
Try 'env --help' for more information.'''.encode('utf-8'))
            return 1
    
    ret = ''
    variables = bash.get_environment_variables()
    for var in variables:
        ret += f'{var}={variables[var]}{line_ending}'
    bash.stdout(ret.encode('utf-8'))
    return 0

info = {
    'command': 'env',
    'path': ['/usr/bin/env', '/bin/env'],
    'help_long': '''Usage: env [OPTION]... [-] [NAME=VALUE]... [COMMAND [ARG]...]
Set each NAME to VALUE in the environment and run COMMAND.

Mandatory arguments to long options are mandatory for short options too.
-i, --ignore-environment  start with an empty environment
-0, --null           end each output line with NUL, not newline
-u, --unset=NAME     remove variable from the environment
-C, --chdir=DIR      change working directory to DIR
-S, --split-string=S  process and split S into separate arguments;
                    used to pass multiple arguments on shebang lines
-v, --debug          print verbose information for each processing step
    --help     display this help and exit
    --version  output version information and exit

A mere - implies -i.  If no COMMAND, print the resulting environment.

GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
Report env translation bugs to <https://translationproject.org/team/>
Full documentation at: <https://www.gnu.org/software/coreutils/env>
or available locally via: info '(coreutils) env invocation\'''',
    'help_short': '',
    'version': '''env (GNU coreutils) 8.30
Copyright (C) 2018 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Written by Richard Mlynarik, David MacKenzie, and Assaf Gordon.''',
    'run': run
}