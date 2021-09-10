from log.logger import logger
from threatshare.session import ThreatSession
import socket

class ConnectionHandler(object):
    def __init__(self, sock: socket.socket, addr):
        self._sock = sock
        self._addr = addr
        self._recv_buf = bytearray()
        self._threat_session = ThreatSession.get_session(addr[0])
        self._handle = True
        self._line_ending = b'\n'
    
    def socket(self) -> socket.socket:
        return self._sock
    
    def remote_address(self):
        return self._addr
    
    def shutdown(self):
        self._threat_session.publish()

        if self._sock:
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
            self._sock = None

    def recv_line(self, max_length: int = 65536) -> bytearray:
        try:
            found_pattern = False
            while True:
                for pattern in [b'\r\n', b'\r\0', b'\n']:
                    pos = self._recv_buf.find(pattern)
                    if pos >= 0:
                        if pattern != b'\n':
                            self._recv_buf = self._recv_buf.replace(pattern, b'\n')
                        found_pattern = True
                        break

                if found_pattern == False:
                    if len(self._recv_buf) > max_length:
                        return None
                    data = self._sock.recv(1)
                    if not data:
                        return None
                    
                    self._recv_buf += data
                else:
                    break
            
            pos = self._recv_buf.find(b'\n')
            ret = self._recv_buf[:pos+1]
            self._recv_buf = self._recv_buf[pos+1:]
            return ret
        except socket.timeout:
            logger.error('Socket timeout waiting for data')
        return None
    
    def recv_until(self, pattern: bytes, max_length: int = 65536) -> bytearray:
        try:
            pos = self._recv_buf.find(pattern)
            while pos < 0:
                data = self._sock.recv(1)
                if not data:
                    return None
                if len(self._recv_buf) > max_length:
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