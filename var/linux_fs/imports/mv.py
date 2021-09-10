from services.bash.handler import BashHandler

def run(bash: BashHandler, executable: str, args: list) -> int:
    vfs = bash.get_vfs()

    files = []
    for arg in args:
        if arg == '--help':
            bash.stdout(info['help_long'].encode('utf-8'))
            return 0
        elif arg[0] == '-':
            bash.stderr(info['help_short'].format(arg).encode('utf-8'))
            return 1
        else:
            files.append(arg)
    
    if len(files) == 0:
        bash.stderr(b'''mv: missing file operand
Try 'mv --help' for more information.''')
        return 1
    elif len(files) == 1:
        bash.stderr(f'''mv: missing destination file operand after '{files[0]}'
Try 'mv --help' for more information.'''.encode('utf-8'))
        return 1
    
    absolute_paths = []
    for file in files:
        if file[0] != vfs._sep:
            absolute_paths.append(vfs.join(bash.get_cwd(), file))
        else:
            absolute_paths.append(file)

    if not vfs.copy(absolute_paths[1], absolute_paths[0], True):
        bash.stderr(f'''mv: cannot stat '{files[0]}': No such file or directory'''.encode('utf-8'))
        return 1
    return 0

info = {
    'command': 'mv',
    'path': ['/usr/bin/mv', '/bin/mv'],
    'help_long': '''Usage: mv [OPTION]... [-T] SOURCE DEST
  or:  mv [OPTION]... SOURCE... DIRECTORY
  or:  mv [OPTION]... -t DIRECTORY SOURCE...
Rename SOURCE to DEST, or move SOURCE(s) to DIRECTORY.

Mandatory arguments to long options are mandatory for short options too.
      --backup[=CONTROL]       make a backup of each existing destination file
  -b                           like --backup but does not accept an argument
  -f, --force                  do not prompt before overwriting
  -i, --interactive            prompt before overwrite
  -n, --no-clobber             do not overwrite an existing file
If you specify more than one of -i, -f, -n, only the final one takes effect.
      --strip-trailing-slashes  remove any trailing slashes from each SOURCE
                                 argument
  -S, --suffix=SUFFIX          override the usual backup suffix
  -t, --target-directory=DIRECTORY  move all SOURCE arguments into DIRECTORY
  -T, --no-target-directory    treat DEST as a normal file
  -u, --update                 move only when the SOURCE file is newer
                                 than the destination file or when the
                                 destination file is missing
  -v, --verbose                explain what is being done
  -Z, --context                set SELinux security context of destination
                                 file to default type
      --help     display this help and exit
      --version  output version information and exit

The backup suffix is '~', unless set with --suffix or SIMPLE_BACKUP_SUFFIX.
The version control method may be selected via the --backup option or through
the VERSION_CONTROL environment variable.  Here are the values:

  none, off       never make backups (even if --backup is given)
  numbered, t     make numbered backups
  existing, nil   numbered if numbered backups exist, simple otherwise
  simple, never   always make simple backups

GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
Report mv translation bugs to <https://translationproject.org/team/>
Full documentation at: <https://www.gnu.org/software/coreutils/mv>
or available locally via: info '(coreutils) mv invocation\'''',
    'help_short': '''mv: invalid option -- '{}'
Try 'mv --help' for more information.''',
    'run': run
}