from services.bash.handler import BashHandler

def run(bash: BashHandler, executable: str, args: list) -> int:
    dirs = []
    auto_dir = False
    for arg in args:
        if arg == '--help':
            bash.stdout(info['help_long'].encode('utf-8'))
            return 0
        elif arg == '-p' or arg == '--parent':
            auto_dir = True
        elif arg[0] != '-':
            dirs.append(arg)
    
    vfs = bash.get_vfs()
    exit_code = 0
    for dir in dirs:
        if dir[0] != vfs._sep:
            target = vfs.join(bash.get_cwd(), dir)
        else:
            target = dir
        
        if not vfs.create_file(target, is_dir=True, auto_dir=auto_dir):
            if vfs.lookup(target):
                bash.stderr(f'mkdir: cannot create directory ‘{dir}’: File exists'.encode('utf-8'))
            else:
                bash.stderr(f'mkdir: cannot create directory ‘{dir}’: No such file or directory'.encode('utf-8'))
            exit_code = 1

    return exit_code

info = {
    'command': 'mkdir',
    'path': ['/usr/bin/mkdir', '/bin/mkdir'],
    'help_long': '''Usage: mkdir [OPTION]... DIRECTORY...
Create the DIRECTORY(ies), if they do not already exist.

Mandatory arguments to long options are mandatory for short options too.
  -m, --mode=MODE   set file mode (as in chmod), not a=rwx - umask
  -p, --parents     no error if existing, make parent directories as needed
  -v, --verbose     print a message for each created directory
  -Z                   set SELinux security context of each created directory
                         to the default type
      --context[=CTX]  like -Z, or if CTX is specified then set the SELinux
                         or SMACK security context to CTX
      --help     display this help and exit
      --version  output version information and exit

GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
Report mkdir translation bugs to <https://translationproject.org/team/>
Full documentation at: <https://www.gnu.org/software/coreutils/mkdir>
or available locally via: info '(coreutils) mkdir invocation\'''',
    'help_short': '',
    'run': run
}