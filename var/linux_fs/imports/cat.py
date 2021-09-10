from services.bash.handler import BashHandler

def run(bash: BashHandler, executable: str, args: list) -> bytes:
    ret = b''
    target_files = []

    for arg in args:
        if arg == '--help':
            bash.stdout(info['help_long'].encode('utf-8'))
            return 0
        elif arg.startswith('-'):
            bash.stderr(info['help_short'].format(arg).encode('utf-8'))
            return 1
        else:
            target_files.append(arg)
    
    exit_code = 1
    vfs = bash.get_vfs()
    if len(target_files) > 0:
        for target in target_files:
            if target[0] != vfs._sep:
                file = vfs.lookup(vfs.join(bash.get_cwd(), target))
            else:
                file = vfs.lookup(target)
            if file:
                if file['type'] == vfs.INODE_TYPE_FILE:
                    exit_code = 0
                    ret += vfs.read_file(file['path'])
                else:
                    bash.stderr(f'cat: {target}: Is a directory'.encode('utf-8'))
                    return 1
            else:
                bash.stderr(f'cat: {target}: No such file or directory'.encode('utf-8'))
                return 1
    
    if len(ret) > 0:
        bash.stdout(ret)
    return exit_code

info = {
    'command': 'cat',
    'path': ['/usr/bin/cat', '/bin/cat'],
    'help_long': '''Usage: cat [OPTION]... [FILE]...                                                                                        Concatenate FILE(s) to standard output.                                                                                                                                                                                                         With no FILE, or when FILE is -, read standard input.                                                                   
  -A, --show-all           equivalent to -vET
  -b, --number-nonblank    number nonempty output lines, overrides -n
  -e                       equivalent to -vE
  -E, --show-ends          display $ at end of each line
  -n, --number             number all output lines
  -s, --squeeze-blank      suppress repeated empty output lines
  -t                       equivalent to -vT
  -T, --show-tabs          display TAB characters as ^I
  -u                       (ignored)
  -v, --show-nonprinting   use ^ and M- notation, except for LFD and TAB
      --help     display this help and exit
      --version  output version information and exit

Examples:
  cat f - g  Output f's contents, then standard input, then g's contents.
  cat        Copy standard input to standard output.

GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
Report cat translation bugs to <https://translationproject.org/team/>
Full documentation at: <https://www.gnu.org/software/coreutils/cat>
or available locally via: info '(coreutils) cat invocation\'''',
    'help_short': '''cat: invalid option -- '{}'
Try 'cat --help' for more information.''',
    'run': run
}