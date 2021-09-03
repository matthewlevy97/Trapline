
from net.connectionhandler import ConnectionHandler
import socket

class TelnetHandler(ConnectionHandler):
    def __init__(self, sock: socket.socket, addr):
        super().__init__(sock, addr)
    
    def handle(self) -> None:
        self._sock.send(b'TESTING')
        self.shutdown()