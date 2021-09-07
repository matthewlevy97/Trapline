from util.shell import ShellHandler
import socket

'''
Commands:
echo
wget
tftp
while do
mkdir
cp
chmod
'''

class BashHandler(ShellHandler):
    KNOWN_COMMANDS = {}
    def __init__(self, sock: socket.socket, addr):
        super().__init__(sock, addr, known_commands=self.KNOWN_COMMANDS)