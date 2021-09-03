from net.server import NetServer
from log.logger import logger
from time import sleep
import os
import select
import signal

class NetManager(object):
    def __init__(self):
        self._servers = {}
        self._epoll = select.epoll()

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

    def run(self) -> None:
        sigchldhandler = signal.getsignal(signal.SIGCHLD)
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        try:
            while True:
                for fileno, event in self._epoll.poll(1):
                    if fileno in self._servers:
                        if event & select.EPOLLIN:
                            self._fork_run(self._servers[fileno].accept_connection)
                        elif event & select.EPOLLHUP:
                            self.del_server(self, self._servers[fileno])
        except KeyboardInterrupt:
            self.shutdown()
        signal.signal(signal.SIGCHLD, sigchldhandler)
    
    def _fork_run(self, function) -> None:
        global logger
        pid = os.fork()
        if pid == 0:
            function()
            import sys; sys.exit(0)
        elif pid == -1:
            logger.error('Failed to fork')
        sleep(0.25)