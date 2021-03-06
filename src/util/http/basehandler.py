
from typing import Any
from net.connectionhandler import ConnectionHandler
from util.http.status import HTTPStatus
from util.config import Config
from threatshare.ioctype import IOCType
from mako.template import Template
from urllib.parse import parse_qs
import email.parser
import os
import socket
import time

'''
    request_line: str
    command: str
    path: str
    request_version: str
    headers: email.message.Message
    contents: bytes
'''
class HTTPBaseHandler(ConnectionHandler):
    _MAX_HEADERS = 64

    server_name = 'HoneyServer'
    protocol_version = 'HTTP/1.1'
    def __init__(self, sock: socket.socket, addr):
        super().__init__(sock, addr)

    def handle(self) -> None:
        self.close_connection = False
        while not self.close_connection:
            if not self.parse_request():
                break
            self._threat_session.add_ioc(IOCType.HTTP_REQUEST, {
                'method': self.command,
                'path': self.path,
                'parameters': self.parameters,
                'http_version': self.request_version,
                'headers': [(header, self.headers[header]) for header in self.headers]
            })
            if self.contents:
                self._threat_session.add_ioc(IOCType.HTTP_REQUEST_DATA, {
                    'content': self.contents
                })

            self.handle_response()
    
    def handle_response(self) -> None:
        raise NotImplementedError

    def load_template(self, template: str, cache: bool = False, **kwargs) -> bytes:
        if cache:
            cache_dir = os.path.join(Config.get('settings.template_directory'), 'cache')
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)

            template = Template(filename=os.path.join(Config.get('settings.template_directory'), template), \
                module_directory=os.path.join(cache_dir, template))
        else:
            template = Template(filename=os.path.join(Config.get('settings.template_directory'), template))
        
        if template:
            return template.render(**kwargs)
        return None

    def parse_request(self) -> bool:
        self.command = None
        self.path = None
        self.parameters = None
        self.request_version = None
        self.headers = None

        self._raw_request = self.recv_until(b'\n')
        if not self._raw_request:
            return False
        if len(self._raw_request) > 65536:
            self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
            return False
        if not self._parse_request():
            return False
        return True

    def decode_form_data(self, data: str) -> dict:
        if data:
            return parse_qs(data)
        return None

    def _parse_request(self) -> bool:
        self.request_line = self._raw_request.decode('latin-1').rstrip('\r\n')
        words = self.request_line.split()
        if len(words) == 0:
            return False
        elif len(words) < 3:
            self.send_error(HTTPStatus.BAD_REQUEST)
            return False

        self.request_version = words[-1]
        self.command, self.raw_path = words[:2]
        if self.raw_path.find('?') > 0:
            pos = self.raw_path.find('?')
            self.path = self.raw_path[:pos]
            self.parameters = parse_qs(self.raw_path[pos+1:])
        else:
            self.path = self.raw_path
            self.parameters = None
        self.headers = self._parse_headers()

        conntype = self.headers.get('Connection', '')
        if conntype.lower() == 'keep-alive':
            self.close_connection = False
        else:
            self.close_connection = True
        
        length = self.headers.get('Content-Length')
        if length:
            try:
                self.contents = self._sock.recv(int(length))
            except:
                self.contents = None
        else:
            self.contents = None
        
        if self.contents:
            self.contents = self.contents.decode('latin-1')
            if not self.parameters and \
            self.headers.get('Content-Type', '') == 'application/x-www-form-urlencoded':
                self.parameters = self.decode_form_data(self.contents)

        return True
    
    def send_error(self, error_code: int) -> None:
        self.add_header('Connection', 'close')
        self.send_response(error_code)
    
    def send_response(self, code: int, message: str = None) -> None:
        if not message:
            message = HTTPStatus.message(code)
        response = f'{self.protocol_version} {code} {message}\r\n'.encode('latin-1')
        self.add_header('Date', self.date_time_string(), True)
        self.add_header('Server', self.server_name, True)

        if hasattr(self, '_content'):
            self.add_header('Content-Type', self._content_type)
            self.add_header('Content-Length', len(self._content))

        if self.close_connection:
            self.add_header('Connection', 'close')
        else:
            self.add_header('Connection', 'keep-alive')

        for header in self._response_headers:
            response += header
        response += b'\r\n'

        if hasattr(self, '_content'):
            response += self._content.encode('latin-1')
        
        self._sock.sendall(response)

    def add_header(self, key: str, value: str, prepend: bool = False) -> None:
        if not hasattr(self, '_response_headers'):
            self._response_headers = []
        
        if prepend:
            self._response_headers.insert(0, (f'{key}: {value}\r\n'.encode('latin-1')))
        else:
            self._response_headers.append((f'{key}: {value}\r\n'.encode('latin-1')))

        if key.lower() == 'connection':
            if value.lower() == 'keep-alive':
                self.close_connection = False
            else:
                self.close_connection = True

    def set_content_type(self, content_type: str) -> None:
        if content_type:
            self._content_type = content_type
        else:
            self._content_type = 'text/html'

    def add_content(self, content: bytes, content_type: str = 'text/html') -> None:
        if not hasattr(self, '_content_type') or not self._content_type:
            if content_type:
                self._content_type = content_type
            else:
                self._content_type = 'text/html'
        if not hasattr(self, '_content'):
            self._content = ''
        self._content += content

    def date_time_string(self, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        return email.utils.formatdate(timestamp, usegmt=True)

    def _parse_headers(self):
        headers = []
        for i in range(self._MAX_HEADERS):
            line = self.recv_line()
            if line in (b'\r\n', b'\n', b''):
                break
            headers.append(line)
        hstring = b''.join(headers).decode('latin-1')
        return email.parser.Parser().parsestr(hstring)