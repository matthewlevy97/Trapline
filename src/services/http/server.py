
from net.server import NetServer
from services.http.handler import HTTPHandler

class HTTPServer(NetServer):
    DEFAULT_PORT = 8080
    def __init__(self, **kwargs):
        super().__init__(HTTPHandler, **kwargs)
        self.create_tcp()
        self.bind(kwargs.get('port', HTTPServer.DEFAULT_PORT))