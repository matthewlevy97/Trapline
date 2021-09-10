from services.bash.handler import BashHandler

RM_FLAG_FORCE = 1
RM_FLAG_RECURSE = 2

def run(bash: BashHandler, executable: str, args: list) -> int:
    targets = []
    flags = 0
    for arg in args:
        if arg == '--help':
            bash.stdout(info['help_long'].encode('utf-8'))
            return 0
        elif len(arg) >= 2 and arg[0] == '-' and arg[1] != '-':
            for miniarg in arg[1:]:
                if miniarg == 'f':
                    flags |= RM_FLAG_FORCE
                elif miniarg == 'r' or miniarg == 'R':
                    flags |= RM_FLAG_RECURSE
        elif arg[0] != '-':
            targets.append(arg)
        else:
            bash.stderr(f'''rm: unrecognized option '{arg}'
Try 'rm --help' for more information.'''.encode('utf-8'))
            return 1
    
    vfs = bash.get_vfs()
    for target in targets:
        if target[0] != vfs._sep:
            target_post = vfs.join(bash.get_cwd(), target)
        else:
            target_post = target
        file = vfs.lookup(target_post)
        if file:
            if file['type'] == vfs.INODE_TYPE_DIRECTORY and (flags & RM_FLAG_RECURSE):
                vfs.rmdir(file['path'])
            elif file['type'] == vfs.INODE_TYPE_FILE:
                vfs.rmfile(file['path'])
            else:
                bash.stderr(f'rm: cannot remove \'{target}\': Is a directory'.encode('utf-8'))
                return 1
        else:
            bash.stderr(f'rm: cannot remove \'{target}\': No such file or directory'.encode('utf-8'))
            return 1
    return 0

info = {
    'command': 'rm',
    'path': ['/usr/bin/rm', '/bin/rm'],
    'help_long': '''Usage: rm [OPTION]... [FILE]...
Remove (unlink) the FILE(s).

  -f, --force           ignore nonexistent files and arguments, never prompt
  -i                    prompt before every removal
  -I                    prompt once before removing more than three files, or
                          when removing recursively; less intrusive than -i,
                          while still giving protection against most mistakes
      --interactive[=WHEN]  prompt according to WHEN: never, once (-I), or
                          always (-i); without WHEN, prompt always
      --one-file-system  when removing a hierarchy recursively, skip any
                          directory that is on a file system different from
                          that of the corresponding command line argument
      --no-preserve-root  do not treat '/' specially
      --preserve-root[=all]  do not remove '/' (default);
                              with 'all', reject any command line argument
                              on a separate device from its parent
  -r, -R, --recursive   remove directories and their contents recursively
  -d, --dir             remove empty directories
  -v, --verbose         explain what is being done
      --help     display this help and exit
      --version  output version information and exit

By default, rm does not remove directories.  Use the --recursive (-r or -R)
option to remove each listed directory, too, along with all of its contents.

To remove a file whose name starts with a '-', for example '-foo',
use one of these commands:
  rm -- -foo

  rm ./-foo

Note that if you use rm to remove a file, it might be possible to recover
some of its contents, given sufficient expertise and/or time.  For greater
assurance that the contents are truly unrecoverable, consider using shred.

GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
Report rm translation bugs to <https://translationproject.org/team/>
Full documentation at: <https://www.gnu.org/software/coreutils/rm>
or available locally via: info '(coreutils) rm invocation\'''',
    'help_short': '',
    'run': run
}