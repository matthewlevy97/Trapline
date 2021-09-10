from services.bash.handler import BashHandler

def run(bash: BashHandler, executable: str, args: list) -> int:
    for arg in args:
        if arg == '--help':
            bash.stdout(info['help_long'].encode('utf-8'))
            return 0
        elif arg.startswith('-'):
            bash.stderr(info['help_short'].format(arg).encode('utf-8'))
            return 1
    bash.stdout(bash.get_cwd().encode('utf-8'))
    return 0

info = {
    'command': 'pwd',
    'path': ['/usr/bin/pwd', '/bin/pwd'],
    'help_long': '''pwd: pwd [-LP]
Print the name of the current working directory.

Options:
    -L        print the value of $PWD if it names the current working
            directory
    -P        print the physical directory, without any symbolic links

By default, `pwd' behaves as if `-L' were specified.

Exit Status:
Returns 0 unless an invalid option is given or the current directory
cannot be read.''',
    'help_short': '''pwd: {}: invalid option
pwd: usage: pwd [-LP]''',
    'run': run
}