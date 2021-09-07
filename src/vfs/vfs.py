from log.logger import logger
from threatshare.ioctype import IOCType
from threatshare.session import ThreatSession
from util.config import Config
from uuid import uuid4
import json
import os
import stat
import time

class VFS(object):
    INODE_TYPE_FILE = 0
    INODE_TYPE_DIRECTORY = 1

    DIRECTORY_SIZE = 4096
    DEFAULT_MODE = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP

    def __init__(self, vfs_config: str):
        self._threat_session = ThreatSession.get_session()
        with open(vfs_config, 'r') as f:
            self._config = json.load(f)
        logger.info(f'Loaded VFS: {self._config["fs_name"]}')
        self._sep = self._config['sep']

        settings = Config.get('settings')
        if settings:
            self._malware_path = settings.get('malware_path', '..')
        else:
            self._malware_path = '..'
    
    '''
    {
        'type': INODE_TYPE_XXX,
        'path': File_Path,
        'real_file': File_Path,
        'import': Py_Import_File_Path, (optional)
    }
    '''
    def lookup(self, path: str) -> dict:
        canonical = self.real_path(path)
        if canonical in self._config['fs']:
            return {
                'path': canonical,
                **self._config['fs'][canonical]
            }
        return None
    
    def create_file(self, path: str, is_dir: bool = False, auto_dir: bool = False) -> bool:
        path_check = ''
        current_time = time.time_ns()
        spath = self.split(path)
        for i in range(len(spath) - 1):
            p = spath[i]
            path_check = self.join(path_check, p)
            if path_check in self._config['fs']:
                if self._config['fs'][path_check]['type'] != self.INODE_TYPE_DIRECTORY:
                    return False
                else:
                    self._config['fs'][path_check]['files'].append(spath[i+1])
            else:
                if auto_dir:
                    d, f = self.basename(path_check)
                    self._config['fs'][d]['files'].append(f)
                    self._config['fs'][path_check] = {
                        'type': self.INODE_TYPE_DIRECTORY,
                        'files': [],
                        'size': self.DIRECTORY_SIZE,
                        'mode': stat.S_IFDIR | self.DEFAULT_MODE,
                        'atime': current_time,
                        'ctime': current_time,
                        'mtime': current_time
                    }
                else:
                    return False
        
        self._config['fs'][path] = {
            'type': self.INODE_TYPE_FILE,
            'size': 0,
            'mode': self.DEFAULT_MODE,
            'atime': current_time,
            'ctime': current_time,
            'mtime': current_time
        }
        if is_dir:
            self._config['fs'][path]['type'] = self.INODE_TYPE_DIRECTORY
            self._config['fs'][path]['size'] = self.DIRECTORY_SIZE
            self._config['fs'][path]['mode'] |= stat.S_IFDIR
        
        return True
    
    def read_file(self, path: str) -> bytes:
        file = self.lookup(path)
        if not file:
            return None
        
        if 'real_path' not in file and file['type'] == self.INODE_TYPE_FILE:
            file['session_created'] = True
            file['real_path'] = self._generate_malware_path(path)
        
        file['atime'] = time.time()
        self._config['fs'][path] = file

        if os.path.isfile(file['real_path']):
            with open(file['real_path'], 'rb') as f:
                data = f.read()
        else:
            data = b''
        self._threat_session.add_ioc(IOCType.FILE_READ, {
            'path': path,
            'real_path': file['real_path'],
            'bytes_read': len(data)
        })
        return data
    
    def write_file(self, path: str, data: bytes, overwrite: bool = True) -> bool:
        file = self.lookup(path)
        if not file:
            return False
        
        if ('real_path' not in file or 'session_created' not in file) and file['type'] == self.INODE_TYPE_FILE:
            file['session_created'] = True
            file['real_path'] = self._generate_malware_path(path)
        
        file['atime'] = time.time()
        file['mtime'] = time.time()

        if overwrite:
            with open(file['real_path'], 'wb') as f:
                f.write(data)
        else:
            with open(file['real_path'], 'ab') as f:
                f.write(data)
        
        old_size = file['size']
        file['size'] = os.stat(file['real_path']).st_size
        self._config['fs'][path] = file
        self._threat_session.add_ioc(IOCType.FILE_WRITE, {
            'path': path,
            'real_path': file['real_path'],
            'new_size': file['size'],
            'old_size': old_size,
            'overwrite': overwrite
        })
        return True
    
    def rmfile(self, path: str) -> bool:
        if path in self._config['fs']:
            self._threat_session.add_ioc(IOCType.FILE_DELETE, {
                'path': path
            })

            d, f = self.basename(path)
            if d in self._config['fs']:
                if self._config['fs'][d]['type'] == self.INODE_TYPE_DIRECTORY:
                    self._config['fs'][d]['files'].remove(f)
            
            self._config['fs'].pop(path)
            return True
        return False

    def rmdir(self, path: str) -> bool:
        if path in self._config['fs']:
            self._threat_session.add_ioc(IOCType.DIRECTORY_DELETE, {
                'path': path
            })

            d, f = self.basename(path)
            if d in self._config['fs']:
                if self._config['fs'][d]['type'] == self.INODE_TYPE_DIRECTORY:
                    self._config['fs'][d]['files'].remove(f)
            
            for key in list(self._config['fs'].keys()):
                if key.startswith(path):
                    self._config['fs'].pop(key)
            return True
        return False

    def basename(self, path: str) -> tuple:
        while path.endswith(self._sep):
            path = path[:-1]
        if not path:
            return ('/', '')
        
        ret = path.rsplit(self._sep, 1)
        if not ret[0]:
            ret[0] = '/'
        return tuple(ret)

    def split(self, path: str) -> list:
        return path.split(self._sep)

    def join(self, path, *paths) -> str:
        while len(path) > 0 and path[-1] == self._sep:
            path = path[:-1]
        
        for p in paths:
            while len(p) > 0 and p[0] == self._sep:
                p = p[1:]
            while len(p) > 0 and p[-1] == self._sep:
                p = p[:-1]
            
            path += self._sep + p
        return path

    def real_path(self, path: str) -> str:
        canonical = []
        for part in path.split(self._sep):
            while len(part) > 0 and part[0] == self._sep:
                part = part[1:]
            while len(part) > 0 and part[-1] == self._sep:
                part = part[:-1]
            
            if not part or part == '.':
                continue
            elif part == '..':
                if len(canonical) > 0:
                    canonical.pop(-1)
            else:
                canonical.append(part)
        return self._sep + self._sep.join(canonical)

    def _generate_malware_path(self, virtual_file_path: str):
        malware_filename = uuid4().hex
        self._threat_session.add_binary(malware_filename, virtual_file_path)
        return self.join(self._malware_path, malware_filename)