from services.bash.handler import BashHandler
from datetime import datetime
import stat

LS_SHOW_INFO = 1
LS_SHOW_HIDDEN = 2
LS_SHOW_HUMAN_READABLE = 4

def run(bash: BashHandler, executable: str, args: list) -> int:
    flags = 0
    target_dir = []

    for arg in args:
        if arg == '--all':
            flags |= LS_SHOW_HIDDEN
        elif arg == '--human-readable':
            flags |= LS_SHOW_HUMAN_READABLE
        elif len(arg) >= 2 and arg[0] == '-' and arg[1] != '-':
            for miniarg in arg[1:]:
                if miniarg == 'l':
                    flags |= LS_SHOW_INFO
                elif miniarg == 'h':
                    flags |= LS_SHOW_HUMAN_READABLE
                elif miniarg == 'a':
                    flags |= LS_SHOW_HIDDEN
                else:
                    bash.stderr(f'''ls: invalid option -- '{miniarg}'
Try 'ls --help' for more information.'''.encode('utf-8'))
                    return 1
        elif arg == '--help':
            bash.stdout(info['help_long'].encode('utf8'))
            return 0
        elif arg == '--version':
            bash.stdout(info['version'].encode('utf-8'))
            return 0
        elif arg[0] != '-':
            target_dir.append(arg)
        else:
            bash.stderr(f'''rm: unrecognized option '{arg}'
Try 'rm --help' for more information.'''.encode('utf-8'))
            return 1
    
    if len(target_dir) == 0:
        target_dir.append(bash.get_cwd())

    exit_code = 1
    ret = b''
    if len(target_dir) > 1:
        for target in target_dir:
            ls_response = _do_ls(bash, target, flags)
            if ls_response != None:
                exit_code = 0
                ret += f'{target}:\r\n'.encode('utf-8')
                if len(ls_response) > 0:
                    ret += ls_response + b'\r\n'
    else:
        ls_response = _do_ls(bash, target_dir[0], flags)
        if ls_response != None:
            exit_code = 0
            if len(ls_response) > 0:
                ret += ls_response + b'\r\n'
    
    if ret:
        bash.stdout(ret)
    return exit_code

def _do_ls(bash: BashHandler, target: str, flags: int) -> int:
    vfs = bash.get_vfs()
    if target[0] != '/':
        target = vfs.join(bash.get_cwd(), target)
    file = vfs.lookup(target)
    if not file:
        bash.stderr(f'ls: cannot access \'{target}\': No such file or directory'.encode('utf-8'))
        return None
    
    ret = b''
    if file['type'] == vfs.INODE_TYPE_DIRECTORY:
        for file_name in file['files']:
            ret += _display_file(bash, vfs, file, file_name, flags)
    elif file['type'] == vfs.INODE_TYPE_FILE:
        ret += _display_file(bash, vfs, file, None, flags)
    return ret

def _display_file(bash, vfs, file, file_name, flags) -> bytes:
    if file_name:
        file = vfs.lookup(vfs.join(file['path'], file_name))
    file_name = vfs.basename(file['path'])[1]

    if flags & LS_SHOW_INFO:
        perm_string = stat.filemode(file.get('mode'))
        file_owner = file.get('owner', bash.get_user())
        file_group = file.get('group', bash.get_user())
        file_size = file.get('size')
        if flags & LS_SHOW_HUMAN_READABLE:
            if file_size > 1073741824:
                file_size = f'{file_size / 1073741824:.1f}G'
            elif file_size > 1048576:
                file_size = f'{file_size / 1048576:.1f}M'
            elif file_size > 1024:
                file_size = f'{file_size / 1024:.1f}K'
        
        file_mod_time = datetime.fromtimestamp(file.get('mtime', 0) // 1000000000) \
            .strftime('%b %d %H:%M')
        ret = f'{perm_string} 1 {file_owner} {file_group} {file_size} {file_mod_time} {file_name}\r\n'
    else:
        ret = f'{file_name} '
    return ret.encode('utf-8')

info = {
    'command': 'ls',
    'path': ['/usr/bin/ls', '/bin/ls'],
    'help_long': '',
    'help_short': '',
    'version': '''ls (GNU coreutils) 8.30
Copyright (C) 2018 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Written by Richard M. Stallman and David MacKenzie.''',
    'run': run
}