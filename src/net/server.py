import socket
from net.connectionhandler import ConnectionHandler
from log.logger import logger

class NetServer(object):
    def __init__(self, handler: ConnectionHandler, **kwargs):
        self._kwargs = kwargs
        self._handler: ConnectionHandler = handler
        self._sock: socket.socket = None
    
    def create_udp(self) -> None:
        if self._sock:
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
            self._sock = None
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def create_tcp(self) -> None:
        if self._sock:
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
            self._sock = None
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def bind(self, port: int, address: str = '127.0.0.1') -> socket.socket:
        global logger
        if self._sock:
            self._sock.bind((address, port))
            self._sock.listen(5)
            logger.info(f'Server bound to {address}:{port}')
        return self._sock
    
    def get_socket(self) -> socket.socket:
        return self._sock

    def accept_connection(self) -> None:
        sock, addr = self._sock.accept()
        handler = self._handler(sock, addr)
        handler.handle()
    
    def shutdown(self) -> None:
        if self._sock:
            self._sock.close()
            self._sock = None