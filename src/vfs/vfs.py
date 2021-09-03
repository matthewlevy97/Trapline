from log.logger import logger
import json

class VFS(object):
    INODE_TYPE_FILE = 0
    INODE_TYPE_DIRECTORY = 1

    def __init__(self, vfs_config: str):
        with open(vfs_config, 'r') as f:
            self._config = json.load(f)
        logger.info(f'Loaded VFS: {self._config["fs_name"]}')
        self._sep = self._config['sep']
    
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
        return {}
    
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
        for p in paths:
            path += self._sep + p
        return path

    def real_path(self, path: str) -> str:
        canonical = []
        for part in path.split(self._sep):
            if not part or part == '.':
                continue
            elif part == '..':
                if len(canonical) > 0:
                    canonical.pop(-1)
            else:
                canonical.append(part)
        return self._sep + self._sep.join(canonical)
