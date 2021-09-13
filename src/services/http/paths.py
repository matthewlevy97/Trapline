from util.http.basehandler import HTTPBaseHandler
from util.http.status import HTTPStatus

class ExploitPaths(object):
    def __init__(self, handler: HTTPBaseHandler):
        self.handler = handler
        
        self._stdout = ''
        self._stderr = ''
        self._exit_code = 0

        self.known_paths = {
            '/robots.txt': self._robots_txt,
            '/cgi-bin/spboard/board.cgi': self._spboard_v4_5,
            '/picsdesc.xml': self._realtek_sdk_miniigd_upnp_soap_rce,
            '/wanipcn.xml': self._realtek_sdk_miniigd_upnp_soap_rce,
            '/setup.cgi': self._setup_cgi,
            '/GponForm/diag_Form': self._gpon_router_auth_bypass,
            '/diag.html': self._gpon_router_auth_bypass
        }

    def handle(self) -> bool:
        if self.handler.path in self.known_paths:
            return self.known_paths[self.handler.path]()
        return False
    
    def _rce(self, cmd: str) -> int:
        if cmd:
            self._stdout, self._stderr, self._exit_code = self.handler.bash.handle_lines([f'{cmd}\r\n'])
            self._stdout = self._stdout.decode('latin-1')
            self._stderr = self._stderr.decode('latin-1')

        self.handler.add_content(
            self.handler.load_template(
                'http/command_execution.html',
                stdout=self._stdout, stderr=self._stderr, exit_code=self._exit_code))
        return self._exit_code

    def _robots_txt(self) -> bool:
        self.handler.add_content(self.handler.load_template('http/robots.txt'), 'text/plain')
        self.handler.send_response(HTTPStatus.OK)
        return True

    def _spboard_v4_5(self) -> bool:
        cmd = self.handler.parameters.get('file', None)
        if cmd:
            cmd = cmd[0].strip('|')
            if len(cmd) > 0:
                self._rce(cmd)
                self.handler.add_header('Content-Disposition', 'attachment; filename="board.cgi"')
                self.handler.send_response(HTTPStatus.OK)
                return True
        return False
    
    def _realtek_sdk_miniigd_upnp_soap_rce(self) -> bool:
        self.handler.server_name = 'miniupnpd/1.0 UPnP/1.0'
        if self.handler.path == '/wanipcn.xml' and self.handler.command == 'POST':
            pos = self.handler.contents.find('NewInternalClient')
            if pos >= 0:
                cmd = self.handler.contents[pos + len('NewInternalClient'):]
                cmd = cmd[:cmd.find('NewInternalClient')]
                # TODO: Handle parsing and executing command
        return False
    
    def _setup_cgi(self) -> bool:
        # Netgear DGN1000 1.1.00.48 'setup.cgi' RCE
        if self.handler.command == 'GET':
            self.handler.add_header('WWW-Authenticate', 'DGN1000')
            cmd = self.handler.parameters.get('cmd', None)
            if cmd:
                self._rce(cmd[0])
                self.handler.send_response(HTTPStatus.OK)
                return True
        return False
    
    def _gpon_router_auth_bypass(self) -> bool:
        if self.handler.path == '/GponForm/diag_Form':
            params = self.handler.parameters
            if 'dest_host' not in params:
                params = self.handler.decode_form_data(self.handler.contents)
                if 'dest_host' not in params:
                    return False
            cmd = params['dest_host'][0]
            if cmd[0] == '`':
                cmd = cmd[1:]
                cmd = cmd[:cmd.find('`')]
            self._rce(cmd)
            self.handler.send_response(HTTPStatus.OK)
        else:
            self._rce(None)
            self.handler.send_response(HTTPStatus.OK)
        return True