from net.server import NetServer
from log.logger import logger
from time import sleep
import os
import select
import signal
import socket

class NetManager(object):
    def __init__(self):
        self._servers = {}
        self._epoll = select.epoll()
        self._running = False

    def add_server(self, server: NetServer) -> bool:
        if not server:
            return False
        
        sock = server.get_socket()
        if not sock:
            return False
        
        fd = sock.fileno()
        self._servers[fd] = server
        self._epoll.register(fd, select.EPOLLIN)
        return True
    
    def del_server(self, server: NetServer) -> bool:
        if not server:
            return False

        sock = server.get_socket()
        if not sock:
            return False

        fd = sock.fileno()
        self._epoll.unregister(fd)
        self._servers[fd].shutdown()
        del self._servers[fd]
    
    def shutdown(self) -> None:
        logger.info(f'Shutting down NetManager: ({len(self._servers)} Servers)')
        while len(self._servers):
            self.del_server(list(self._servers.values())[0])

    def stop(self, signum, frame) -> None:
        self._running = False
    
    def run(self) -> None:
        self.default_sigint = signal.getsignal(signal.SIGINT)
        self.default_sigterm = signal.getsignal(signal.SIGTERM)

        sigchldhandler = signal.getsignal(signal.SIGCHLD)
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

        self._running = True
        while self._running:
            try:
                for fileno, event in self._epoll.poll(1):
                    if fileno in self._servers:
                        if event & select.EPOLLIN:
                            self._fork_run(self._servers[fileno].accept_connection)
                        elif event & select.EPOLLHUP:
                            self.del_server(self, self._servers[fileno])
            except socket.timeout:
                pass
        self.shutdown()
        signal.signal(signal.SIGCHLD, sigchldhandler)
        signal.signal(signal.SIGINT, self.default_sigint)
        signal.signal(signal.SIGTERM, self.default_sigterm)
    
    def _fork_run(self, function) -> None:
        global logger
        pid = os.fork()
        if pid == 0:
            try:
                signal.signal(signal.SIGINT, self.default_sigint)
                signal.signal(signal.SIGTERM, self.default_sigterm)
                function()
            finally:
                os._exit(0)
        elif pid == -1:
            logger.error('Failed to fork')
        sleep(0.25)