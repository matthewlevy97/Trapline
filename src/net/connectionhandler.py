from log.logger import logger
import socket

class ConnectionHandler(object):
    def __init__(self, sock: socket.socket, addr):
        self._sock = sock
        self._addr = addr
        self._recv_buf = bytearray()
    
    def socket(self) -> socket.socket:
        return self._sock
    
    def remote_address(self):
        return self._addr
    
    def shutdown(self):
        if self._sock:
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
            self._sock = None

    def recv_until(self, pattern: bytes) -> bytearray:
        try:
            pos = self._recv_buf.find(pattern)
            while pos < 0:
                data = self._sock.recv(512)
                if not data:
                    return None
                
                self._recv_buf += data
                pos = self._recv_buf.find(pattern)
            ret = self._recv_buf[:pos+1]
            self._recv_buf = self._recv_buf[pos+1:]
            return ret
        except socket.timeout:
            logger.error('Socket timeout waiting for data')
        return None
    
    def handle(self) -> None:
        raise NotImplementedError