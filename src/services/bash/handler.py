
from log.logger import logger
from vfs.linux import LinuxVFS
from net.connectionhandler import ConnectionHandler
import importlib.util
import socket
import sys
import re

class BashHandler(ConnectionHandler):
    SHELL_NAME = "/bin/bash"

    def __init__(self, sock: socket.socket, addr):
        super().__init__(sock, addr)
        self._vfs = LinuxVFS()
        self._known_commands = {
            'cd': self._do_cd,
            'exit': self._do_exit,
            'help': self._do_help,
            'history': self._do_history,
            'logout': self._do_logout
        }

        self._history = []
        self._environment = {}
        self._user: str = 'root'
        perms = self.lookup_user_perms(self._user)
        self._gid: int = perms['gid']
        self._uid: int = perms['uid']
        self._home_dir: str = perms['home_dir']
        self._cwd: str = self._home_dir
        self.set_environment_variable('SHELL', self.SHELL_NAME)
        self.set_environment_variable('PATH', '/usr/bin:/bin:.')
        self.set_environment_variable('USER', self._user)
        self.set_environment_variable('HOME', self._home_dir)
        self.set_environment_variable('PWD', self._cwd)
    
    def get_user(self) -> str:
        return self._user

    def lookup_user_perms(self, user: str):
        return {
            'uid': 0,
            'gid': 0,
            'home_dir': '/'
        }

    def set_cwd(self, path: str) -> None:
        self.set_environment_variable('PWD', path)
        self._cwd = path
    
    def get_cwd(self) -> str:
        return self._cwd
    def get_home_dir(self, path: str) -> None:
        return self._home_dir
    
    def get_vfs(self) -> LinuxVFS:
        return self._vfs

    def set_environment_variable(self, variable: str, value: str) -> None:
        key = self._env_var_to_regex(variable)
        self._environment[key] = value
    
    def unset_environment_variable(self, variable: str, value: str) -> None:
        key = self._env_var_to_regex(variable)
        del self._environment[key]

    def get_environment_variables(self) -> dict:
        env_vars = {}
        for var in self._environment:
            tmp = var.pattern
            tmp = tmp[tmp.find('{')+1:]
            tmp = tmp[:tmp.find('}')]
            env_vars[tmp] = self._environment[var]
        return env_vars
    
    def get_environment_variable(self, variable: str) -> str:
        for var in self._environment:
            tmp = var.pattern
            tmp = tmp[tmp.find('{')+1:]
            tmp = tmp[:tmp.find('}')]
            if tmp == variable:
                return self._environment[var]
        return None

    def handle(self) -> None:
        while True:
            if self._uid == 0:
                self._sock.sendall(self.root_prompt())
            else:
                self._sock.sendall(self.user_prompt())
            
            line = self.recv_until(b"\n")
            if not line:
                break
            
            response = self._generate_response(line)
            if response:
                self._sock.sendall(response)
        
        self.shutdown()
    
    def root_prompt(self) -> bytes:
        return b'# '
    def user_prompt(self) -> bytes:
        return b'$ '
    
    def _env_var_to_regex(self, variable: str):
        return re.compile(r'\$({%s}|%s((?=\s)|$))' % (variable, variable))

    def _generate_response(self, line: bytearray) -> bytes:
        ret = b''
        self._history.append(line.decode('utf-8'))
        for command in line.split(b';'):
            command = self._expand_variables(command.decode('utf-8'))
            args = command.split()
            if len(args) < 1:
                continue

            executable = args[0]
            if executable in self._known_commands:
                output = self._known_commands[executable](args[1:])
            else:
                output = self._lookup_executable(executable, args[1:])
            
            if output != None:
                ret += output
            else:
                ret += self._command_not_found(executable)
            
            if not ret.endswith(b'\r\n'):
                ret += b'\r\n'
            
        return ret
    
    def _command_not_found(self, executable: str) -> bytes:
        if executable.find('/') >= 0:
            return f'{executable}: No such file or directory'.encode('utf-8')
        return f'{executable}: command not found'.encode('utf-8')

    def _expand_variables(self, data: str) -> str:
        for env_var in self._environment:
            data = env_var.sub(self._environment[env_var], data)
        data = data.replace('~', self._home_dir)
        return data

    def _lookup_executable(self, executable, args) -> bytes:
        file = self._vfs.lookup(executable)
        if not file:
            paths = self.get_environment_variable('PATH')
            for path in paths.split(':'):
                file = self._vfs.lookup(self._vfs.join(path, executable))
                if file:
                    break
        
        if file:
            if file['type'] == self._vfs.INODE_TYPE_DIRECTORY:
                return f'{file["path"]}: Is a directory'.encode('utf-8')
            elif file['type'] == self._vfs.INODE_TYPE_FILE:
                if 'import' in file:
                    return self._import_and_execute(file, executable, args)
                else:
                    return f'{file["path"]}: Permission denied'.encode('utf-8')
        return None
    
    def _import_and_execute(self, file: dict, executable, args) -> bytes:
        import_name = f'bash.{executable}'

        if import_name not in sys.modules:
            logger.info(f'Importing: {file["import"]}')
            spec = importlib.util.spec_from_file_location(import_name, file['import'])
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            sys.modules[import_name] = mod
        else:
            mod = sys.modules[import_name]

        if hasattr(mod, 'info'):
            info = mod.__getattribute__('info')
            if 'run' in info:
                return info['run'](self, args)
        return None

    def _do_cd(self, args) -> bytes:
        target_path = None
        for arg in args:
            if arg == '--help':
                return b'''cd: cd [-L|[-P [-e]] [-@]] [dir]
    Change the shell working directory.

    Change the current directory to DIR.  The default DIR is the value of the
    HOME shell variable.

    The variable CDPATH defines the search path for the directory containing
    DIR.  Alternative directory names in CDPATH are separated by a colon (:).
    A null directory name is the same as the current directory.  If DIR begins
    with a slash (/), then CDPATH is not used.

    If the directory is not found, and the shell option `cdable_vars' is set,
    the word is assumed to be  a variable name.  If that variable has a value,
    its value is used for DIR.

    Options:
      -L        force symbolic links to be followed: resolve symbolic
                links in DIR after processing instances of `..'
      -P        use the physical directory structure without following
                symbolic links: resolve symbolic links in DIR before
                processing instances of `..'
      -e        if the -P option is supplied, and the current working
                directory cannot be determined successfully, exit with
                a non-zero status
      -@        on systems that support it, present a file with extended
                attributes as a directory containing the file attributes

    The default is to follow symbolic links, as if `-L' were specified.
    `..' is processed by removing the immediately previous pathname component
    back to a slash or the beginning of DIR.

    Exit Status:
    Returns 0 if the directory is changed, and if $PWD is set successfully when
    -P is used; non-zero otherwise.'''
            elif arg.startswith('-') and len(arg) > 1:
                return f'''cd: {arg}: invalid option
cd: usage: cd [-L|[-P [-e]] [-@]] [dir]'''.encode('utf-8')
            elif not target_path:
                target_path = arg
            else:
                return b'cd: too many arguments'
        
        if target_path == '~' or not target_path:
            target_path = self._home_dir
        if target_path[0] == '.':
            if len(target_path) == 1 or target_path[1] != '.':
                target_path = self._vfs.join(self._cwd, target_path[1:])
        if target_path[0] != '/':
            target_path = self._vfs.join(self._cwd, target_path)

        file = self._vfs.lookup(target_path)
        if file:
            if file['type'] != self._vfs.INODE_TYPE_DIRECTORY:
                return f'cd: {target_path}: Not a directory'.encode('utf-8')
            else:
                self.set_cwd(file['path'])
                return b''
        else:
            return f'cd: {target_path}: No such file or directory'.encode('utf-8')
    
    def _do_exit(self, args) -> bytes:
        return b'exit'
    
    def _do_help(self, args) -> bytes:
        return b'''GNU bash, version 5.0.17(1)-release (x86_64-pc-linux-gnu)
These shell commands are defined internally.  Type `help' to see this list.
Type `help name' to find out more about the function `name'.
Use `info bash' to find out more about the shell in general.
Use `man -k' or `info' to find out more about commands not in this list.

A star (*) next to a name means that the command is disabled.

 job_spec [&]                                                             history [-c] [-d offset] [n] or history -anrw [filename] or history ->
 (( expression ))                                                         if COMMANDS; then COMMANDS; [ elif COMMANDS; then COMMANDS; ]... [ el>
 . filename [arguments]                                                   jobs [-lnprs] [jobspec ...] or jobs -x command [args]
 :                                                                        kill [-s sigspec | -n signum | -sigspec] pid | jobspec ... or kill -l>
 [ arg... ]                                                               let arg [arg ...]
 [[ expression ]]                                                         local [option] name[=value] ...
 alias [-p] [name[=value] ... ]                                           logout [n]
 bg [job_spec ...]                                                        mapfile [-d delim] [-n count] [-O origin] [-s count] [-t] [-u fd] [-C>
 bind [-lpsvPSVX] [-m keymap] [-f filename] [-q name] [-u name] [-r key>  popd [-n] [+N | -N]
 break [n]                                                                printf [-v var] format [arguments]
 builtin [shell-builtin [arg ...]]                                        pushd [-n] [+N | -N | dir]
 caller [expr]                                                            pwd [-LP]
 case WORD in [PATTERN [| PATTERN]...) COMMANDS ;;]... esac               read [-ers] [-a array] [-d delim] [-i text] [-n nchars] [-N nchars] [>
 cd [-L|[-P [-e]] [-@]] [dir]                                             readarray [-d delim] [-n count] [-O origin] [-s count] [-t] [-u fd] [>
 command [-pVv] command [arg ...]                                         readonly [-aAf] [name[=value] ...] or readonly -p
 compgen [-abcdefgjksuv] [-o option] [-A action] [-G globpat] [-W wordl>  return [n]
 complete [-abcdefgjksuv] [-pr] [-DEI] [-o option] [-A action] [-G glob>  select NAME [in WORDS ... ;] do COMMANDS; done
 compopt [-o|+o option] [-DEI] [name ...]                                 set [-abefhkmnptuvxBCHP] [-o option-name] [--] [arg ...]
 continue [n]                                                             shift [n]
 coproc [NAME] command [redirections]                                     shopt [-pqsu] [-o] [optname ...]
 declare [-aAfFgilnrtux] [-p] [name[=value] ...]                          source filename [arguments]
 dirs [-clpv] [+N] [-N]                                                   suspend [-f]
 disown [-h] [-ar] [jobspec ... | pid ...]                                test [expr]
 echo [-neE] [arg ...]                                                    time [-p] pipeline
 enable [-a] [-dnps] [-f filename] [name ...]                             times
 eval [arg ...]                                                           trap [-lp] [[arg] signal_spec ...]
 exec [-cl] [-a name] [command [arguments ...]] [redirection ...]         true
 exit [n]                                                                 type [-afptP] name [name ...]
 export [-fn] [name[=value] ...] or export -p                             typeset [-aAfFgilnrtux] [-p] name[=value] ...
 false                                                                    ulimit [-SHabcdefiklmnpqrstuvxPT] [limit]
 fc [-e ename] [-lnr] [first] [last] or fc -s [pat=rep] [command]         umask [-p] [-S] [mode]
 fg [job_spec]                                                            unalias [-a] name [name ...]
 for NAME [in WORDS ... ] ; do COMMANDS; done                             unset [-f] [-v] [-n] [name ...]
 for (( exp1; exp2; exp3 )); do COMMANDS; done                            until COMMANDS; do COMMANDS; done
 function name { COMMANDS ; } or name () { COMMANDS ; }                   variables - Names and meanings of some shell variables
 getopts optstring name [arg]                                             wait [-fn] [id ...]
 hash [-lr] [-p pathname] [-dt] [name ...]                                while COMMANDS; do COMMANDS; done
 help [-dms] [pattern ...]                                                { COMMANDS ; }'''
    
    def _do_history(self, args) -> bytes:
        ret = ''
        for i in range(len(self._history)):
            ret += f'{i} {self._history[i]}'
        return ret.encode('utf-8')
    
    def _do_logout(self, args) -> bytes:
        return b'logout'
