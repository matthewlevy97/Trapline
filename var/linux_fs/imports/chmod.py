from services.bash.handler import BashHandler
import stat

def run(bash: BashHandler, executable: str, args: list) -> int:
    recursive = False
    mode = None
    files = []

    for arg in args:
        if arg == '--help':
            bash.stdout(info['help_long'].encode('utf-8'))
            return 0
        if arg == '--recursive':
            recursive = True
        elif len(arg) > 1 and arg[0] == '-' and arg[1] != '-':
            for miniarg in arg[1:]:
                if miniarg == 'R':
                    recursive = True
                if miniarg in 'xrw':
                    mode = '-' + miniarg
                else:
                    bash.stderr(info['help_short'].format(miniarg).encode('utf-8'))
                    return 1
        elif arg == '-':
            bash.stderr(info['help_short'].format(arg.strip('-')).encode('utf-8'))
            return 1
        elif mode == None:
            mode = arg
        else:
            files.append(arg)
    
    if mode == None:
        bash.stderr(b'''chmod: missing operand
Try 'chmod --help' for more information.'''.encode('utf-8'))
        return 1
    if len(files) == 0:
        bash.stderr(f'''chmod: missing operand after ‘{mode}’
Try 'chmod --help' for more information.)'''.encode('utf-8'))
        return 1
    
    vfs = bash.get_vfs()
    exit_code = 1

    for file in files:
        if file[0] != vfs._sep:
            absolute_path = vfs.join(bash.get_cwd(), file)
        else:
            absolute_path = file
        
        f = vfs.lookup(absolute_path)
        if f:
            if mode[0] == '-' or mode[0] == '+':
                octal_mode = _convert_to_octal(f['mode'], mode)
            else:
                try:
                    octal_mode = int(mode, 8)
                except ValueError:
                    bash.stderr(f'''chmod: invalid mode: ‘{mode}’
            Try 'chmod --help' for more information.'''.encode('utf-8'))
                    return 1
        else:
            try:
                octal_mode = int(mode, 8)
            except ValueError:
                bash.stderr(f'''chmod: invalid mode: ‘{mode}’
        Try 'chmod --help' for more information.'''.encode('utf-8'))
                return 1

        if not vfs.chmod(absolute_path, octal_mode, recursive):
            bash.stderr(f'chmod: cannot access \'{file}\': No such file or directory'.encode('utf-8'))
        else:
            exit_code = 0
    return exit_code

def _convert_to_octal(original_mode: int, mode: str) -> int:
    ret = original_mode

    remove = False
    for c in mode:
        if c == '-':
            remove = True
        elif c == '+':
            remove = False
        
        if remove:
            if c == 'x':
                ret &= ~(stat.S_IXUSR | stat.S_IXGRP)
            elif c == 'r':
                ret &= ~(stat.S_IRUSR | stat.S_IRGRP)
            elif c == 'w':
                ret &= ~(stat.S_IWUSR | stat.S_IWGRP)
        else:
            if c == 'x':
                ret |= (stat.S_IXUSR | stat.S_IXGRP)
            elif c == 'r':
                ret |= (stat.S_IRUSR | stat.S_IRGRP)
            elif c == 'w':
                ret |= (stat.S_IWUSR | stat.S_IWGRP)
    return ret

info = {
    'command': 'chmod',
    'path': ['/usr/bin/chmod', '/bin/chmod'],
    'help_long': '''Usage: chmod [OPTION]... MODE[,MODE]... FILE...
  or:  chmod [OPTION]... OCTAL-MODE FILE...
  or:  chmod [OPTION]... --reference=RFILE FILE...
Change the mode of each FILE to MODE.
With --reference, change the mode of each FILE to that of RFILE.

  -c, --changes          like verbose but report only when a change is made
  -f, --silent, --quiet  suppress most error messages
  -v, --verbose          output a diagnostic for every file processed
      --no-preserve-root  do not treat '/' specially (the default)
      --preserve-root    fail to operate recursively on '/'
      --reference=RFILE  use RFILE's mode instead of MODE values
  -R, --recursive        change files and directories recursively
      --help     display this help and exit
      --version  output version information and exit

Each MODE is of the form '[ugoa]*([-+=]([rwxXst]*|[ugo]))+|[-+=][0-7]+'.

GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
Report chmod translation bugs to <https://translationproject.org/team/>
Full documentation at: <https://www.gnu.org/software/coreutils/chmod>
or available locally via: info '(coreutils) chmod invocation\'''',
    'help_short': '''chmod: invalid option -- '{}'
Try 'chmod --help' for more information.''',
    'run': run
}