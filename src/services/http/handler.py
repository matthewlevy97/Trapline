from util.http.basehandler import HTTPBaseHandler
from util.http.status import HTTPStatus

class HTTPHandler(HTTPBaseHandler):
    def handle_response(self) -> None:
        self.add_content(b'<html></html>', 'text/html')
        self.send_response(HTTPStatus.OK)