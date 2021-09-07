
from log.logger import logger
from util.commandparser import CommandParser
from vfs.linux import LinuxVFS
from net.connectionhandler import ConnectionHandler
from vfs.vfs import VFS
import importlib.util
import socket
import sys
import re

class ShellHandler(ConnectionHandler):
    SHELL_NAME = "/bin/bash"

    def __init__(self, sock: socket.socket, addr, vfs: VFS = None, known_commands: dict = {}):
        super().__init__(sock, addr)
        if not vfs:
            vfs = LinuxVFS()
        self._vfs = vfs
        self._known_commands = known_commands
        self._known_commands['cd'] = self._do_cd
        self._known_commands['exit'] = self._do_exit
        self._known_commands['history'] = self._do_history

        self._root_prompt = b'# '
        self._user_prompt = b'$ '

        self._command_parser = CommandParser()

        self._history = []
        self._environment = {}
        self._stdin: bytes = None
        self._stdout: bytes = None
        self._stderr: bytes = None
        self._exit_code = 0
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
    
    def stdin(self, data: bytes = None) -> bytes:
        if data:
            if self._stdin:
                self._stdin += data
            else:
                self._stdin = data
        return self._stdin
    def stdout(self, data: bytes = None) -> bytes:
        if data:
            if self._stdout:
                self._stdout += b'\r\n' + data
            else:
                self._stdout = data
        return self._stdout
    def stderr(self, data: bytes = None) -> bytes:
        if data:
            if self._stderr:
                self._stderr += b'\r\n' + data
            else:
                self._stderr = data
        return self._stderr

    def get_exit_code(self) -> int:
        return self._exit_code

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

    def handle_lines(self, lines: list) -> tuple:
        stdout = b''
        stderr = b''
        for line in lines:
            tmp_stdout, tmp_stderr, exit_code = self._generate_response(line)
            stdout += tmp_stdout
            stderr += tmp_stderr
            if exit_code:
                break
        return (stdout, stderr, exit_code)

    def handle(self) -> None:
        while self._handle:
            if self._uid == 0:
                self._sock.sendall(self._root_prompt)
            else:
                self._sock.sendall(self._user_prompt)
            
            line = self.recv_until(b'\n')
            if not line:
                break
            
            stdout, stderr, _ = self._generate_response(line)
            if stderr:
                self._sock.sendall(stderr)
            if stdout:
                self._sock.sendall(stdout)
        
        self.shutdown()
    
    def _env_var_to_regex(self, variable: str):
        return re.compile(r'\$({%s}|%s((?=\s)|$))' % (variable, variable))

    def _generate_response(self, line: bytearray) -> tuple:
        ret_stdout = b''
        ret_stderr = b''
        line = self._expand_variables(line.decode('utf-8'))
        self._history.append(line)
        self._command_parser.feed(line)
        commands, parse_error = self._command_parser.parse()
        if parse_error:
            return (None, parse_error.encode('utf-8'), 1)

        for command in commands:
            self._stdin = None
            self._stdout = None
            self._stderr = None
            while command and self._handle:
                if command['executable'] == None:
                    break

                if 'redirect' in command and 'stdin' in command['redirect']:
                    stdin_filename = command['redirect']['stdin']['file']
                    if stdin_filename[0] != self._vfs._sep:
                        file = self._vfs.lookup(self._vfs.join(self._cwd, stdin_filename))
                    else:
                        file = self._vfs.lookup(stdin_filename)
                    if not file:
                        self.stderr(f'{stdin_filename}: No such file or directory'.encode('utf-8'))
                        break
                    elif file['type'] == self._vfs.INODE_TYPE_FILE:
                        self._stdin = self._vfs.read_file(file['path'])

                executable = command['executable']
                if executable in self._known_commands:
                    self._exit_code = self._known_commands[executable](command['args'])
                else:
                    self._exit_code = self._lookup_executable(executable, command['args'])
            
                if self._stdout == None and self._stderr == None and self._exit_code:
                    self._command_not_found(executable)

                if 'redirect' in command and ('stdout' in command['redirect'] or 'stderr' in command['redirect']):
                    self._redirect(command['redirect'])
                if 'pipe' in command:
                    command = command['pipe']
                    self._stdin = self._stdout if self._stdout != None else self._stderr
                elif 'conditional_or' in command and self._exit_code != 0:
                    command = command['conditional_or']
                elif 'conditional_and' in command and self._exit_code == 0:
                    command = command['conditional_and']
                else:
                    if self._stderr != b'' and self._stderr != None:
                        ret_stderr += self._stderr
                        if not ret_stderr.endswith(b'\r\n'):
                            ret_stderr += b'\r\n'
                    if self._stdout != b'' and self._stdout != None:
                        ret_stdout += self._stdout
                        if not ret_stdout.endswith(b'\r\n'):
                            ret_stdout += b'\r\n'
                    command = None

            if not self._handle:
                break
                
        return (ret_stdout, ret_stderr, self._exit_code)

    def _redirect(self, redirection: dict, target: str = None) -> None:
        if target == None:
            self._redirect(redirection, 'stdout')
            self._redirect(redirection, 'stderr')
        else:
            if target in redirection:
                fname = redirection[target]['file']
                if fname[0] != self._vfs._sep:
                    fname = self._vfs.join(self._cwd, fname)
                file = self._vfs.lookup(fname)
                if file == None and self._vfs.create_file(fname):
                    file = self._vfs.lookup(fname)

                if file:
                    self._vfs.write_file(file['path'], self._stdout, redirection[target]['overwrite'])
                    setattr(self, f'_{target}', None)
                else:
                    if target == 'stderr':
                        self._stderr = f'{fname}: No such file or directory'.encode('utf-8')
                    else:
                        self.stderr(f'{fname}: No such file or directory'.encode('utf-8'))
    
    def _command_not_found(self, executable: str) -> bytes:
        if executable.find('/') >= 0:
            self.stderr(f'{executable}: No such file or directory'.encode('utf-8'))
        self.stderr(f'{executable}: command not found'.encode('utf-8'))

    def _expand_variables(self, data: str) -> str:
        for env_var in self._environment:
            data = env_var.sub(self._environment[env_var], data)
        data = data.replace('~', self._home_dir)
        return data

    def _lookup_executable(self, executable: str, args: list) -> int:
        file = self._vfs.lookup(executable)
        if not file:
            paths = self.get_environment_variable('PATH')
            for path in paths.split(':'):
                file = self._vfs.lookup(self._vfs.join(path, executable))
                if file:
                    break
        
        if file:
            if file['type'] == self._vfs.INODE_TYPE_DIRECTORY:
                self.stderr(f'{file["path"]}: Is a directory'.encode('utf-8'))
                return 1
            elif file['type'] == self._vfs.INODE_TYPE_FILE:
                if 'import' in file:
                    return self._import_and_execute(file, executable, args)
                else:
                    self.stderr(f'{file["path"]}: Permission denied'.encode('utf-8'))
                    return 1
        return 1
    
    def _import_and_execute(self, file: dict, executable: str, args: list) -> bytes:
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
                return info['run'](self, executable, args)
        return 1

    def _do_cd(self, args) -> int:
        target_path = None
        for arg in args:
            if arg == '--help':
                self.stdout(b'''cd: cd [-L|[-P [-e]] [-@]] [dir]
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
    -P is used; non-zero otherwise.''')
                return 0
            elif arg.startswith('-') and len(arg) > 1:
                self.stderr(f'''cd: {arg}: invalid option
cd: usage: cd [-L|[-P [-e]] [-@]] [dir]'''.encode('utf-8'))
                return 2
            elif not target_path:
                target_path = arg
            else:
                self.stderr(b'cd: too many arguments')
                return 1
        
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
                self.stderr(f'cd: {target_path}: Not a directory'.encode('utf-8'))
                return 1
            else:
                self.set_cwd(file['path'])
                return 0
        else:
            self.stderr(f'cd: {target_path}: No such file or directory'.encode('utf-8'))
            return 1
    
    def _do_history(self, args) -> int:
        ret = ''
        for i in range(len(self._history)):
            ret += f'{i} {self._history[i]}'
        self.stdout(ret.encode('utf-8'))
        return 0
    
    def _do_exit(self, args) -> int:
        self._exit_code = 0
        self._handle = False
        return 0
