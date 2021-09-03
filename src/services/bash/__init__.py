
from net.server import NetServer
from services.bash.handler import BashHandler

class BashServer(NetServer):
    def __init__(self, **kwargs):
        super().__init__(BashHandler, **kwargs)
        self.create_tcp()
        self.bind(kwargs.get('port', 4444))

metadata = {
    'name': 'Bash',
    'description': 'Emulation of Bash shell',
    'server': BashServer
}