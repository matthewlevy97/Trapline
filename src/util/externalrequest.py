from typing import Any
import requests

class ExternalRequest(object):

    @staticmethod
    def web_request(url: str, method: str = 'GET', data: Any = None) -> bytes:
        headers = {
            
        }
        requests.request(method=method, url=url, headers=headers, data=data)