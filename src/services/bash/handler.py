from util.shell.shell import ShellHandler
import socket

'''
Commands:
tftp
kill
killall
curl
date
crontab
'''

class BashHandler(ShellHandler):
    KNOWN_COMMANDS = {}
    def __init__(self, sock: socket.socket, addr):
        super().__init__(sock, addr, known_commands=self.KNOWN_COMMANDS)
    
    def _command_not_found(self, executable: str) -> bytes:
        if executable.find('/') >= 0:
            self.stderr(f'{executable}: No such file or directory'.encode('latin-1'))
        self.stderr(f'{executable}: applet not found'.encode('latin-1'))