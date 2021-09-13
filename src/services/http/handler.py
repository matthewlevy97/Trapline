from services.http.paths import ExploitPaths
from util.http.basehandler import HTTPBaseHandler
from util.http.status import HTTPStatus
from util.shell.shell import ShellHandler
import socket

class HTTPHandler(HTTPBaseHandler):
    def __init__(self, sock: socket.socket, addr):
        super().__init__(sock, addr)
        self.bash = ShellHandler(self._sock, self._addr)
        self._exploit_paths = ExploitPaths(self)
    
    def shutdown(self):
        if self.bash:
            self.bash.shutdown(False)
        return super().shutdown()
    
    def handle_response(self) -> None:
        if self._exploit_detection():
            return
        
        self.add_content('<html><body>Index of <body></html>')
        self.send_response(HTTPStatus.OK)
    
    def _exploit_detection(self) -> bool:
        if self._exploit_paths.handle():
            pass
        else:
            return False
        return True