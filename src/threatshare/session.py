from log.logger import logger
from io import BytesIO
from uuid import uuid4
import hashlib
import json
import os
import requests
import tarfile
from threatshare.ioctype import IOCType

from util.config import Config

class ThreatSession(object):
    @staticmethod
    def get_session(remote_host: str = None):
        global _threat_session
        if _threat_session:
            return _threat_session
        if remote_host:
            _threat_session = ThreatSession(remote_host)
        return _threat_session

    def __init__(self, remote_host: str):
        self._session_id = uuid4().hex
        self._adversary_id = hashlib.sha256(remote_host.encode('utf-8')).hexdigest()
        self._metadata = {
            'session_id': self._session_id,
            'adversary_id': self._adversary_id,
            'remote_host': remote_host,
            'ioc': [],
            'binary': []
        }
        settings = Config.get('settings')
        if settings:
            self._malware_path = settings.get('malware_path', '../staging')
        
        publish = Config.get('publish')
        if publish:
            self._staging_path = publish.get('staging_path', '../staging')
            self._delete_after_publish = publish.get('delete_after_publish', True)
            self._publish_uri = publish.get('publish_uri', None)
        else:
            self._malware_path = '../malware'
            self._staging_path = '../staging'
            self._delete_after_publish = True
            self._publish_uri = None
    
    def add_ioc(self, type: int, ioc: dict) -> None:
        if len(self._metadata['ioc']) > 0:
            previous = self._metadata['ioc'][-1]
            match = True
            for key in previous.keys():
                if key == 'type' and previous['type'] != type:
                    match = False
                    break
                elif key in ioc and previous[key] != ioc[key]:
                    match = False
                    break    
            if match:
                return
        
        self._metadata['ioc'].append({
            'type': type,
            **ioc
        })
    
    def add_binary(self, filename: str, virtual_path: str = None) -> None:
        self.add_ioc(IOCType.BINARY_FILE, {
            'binary': filename,
            'path': virtual_path
        })
        self._metadata['binary'].append(filename)
    
    def publish(self) -> None:
        staging_file = os.path.join(self._staging_path, f'{self._session_id}.tgz')
        with tarfile.open(staging_file, mode='w:gz') as tar:
            data = json.dumps(self._metadata).encode('utf-8')
            info = tarfile.TarInfo(name="metadata.json")
            info.size = len(data)
            with BytesIO(data) as io:
                tar.addfile(tarinfo=info, fileobj=io)
            
            i = 0
            while i < len(self._metadata['binary']):
                binary = self._metadata['binary'][i]
                if not os.path.isfile(binary):
                    self._metadata['binary'].pop(i)
                    continue
                tar.add(f'{os.path.join(self._malware_path, binary)}', binary)
        
        if self._publish_uri:
            requests.post(self._publish_uri, files={'file': open(staging_file, 'rb')})
        if self._delete_after_publish:
            os.remove(staging_file)
        logger.info(f'Published Threat Intel: [SessionID: {self._session_id}]')

_threat_session: ThreatSession = None