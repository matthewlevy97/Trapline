
from net.server import NetServer
from services.telnet.handler import TelnetHandler

class TelnetServer(NetServer):
    DEFAULT_PORT = 2323
    def __init__(self, **kwargs):
        super().__init__(TelnetHandler, **kwargs)
        self.create_tcp()
        self.bind(kwargs.get('port', TelnetServer.DEFAULT_PORT))