from vfs.vfs import VFS
import importlib.util
import copy
import json
import os

class MakeVFS(object):
    def __init__(self, root_dir: str, name: str = 'VirtualFileSystem', sep: str = os.path.sep):
        self._root_dir = root_dir
        self._name = name
        self._sep = sep
    
    def generate(self) -> dict:
        vfs = self._generate_vfs()
        self._add_imports(vfs)
        return {
            'fs_name': self._name,
            'sep': self._sep,
            'fs': vfs
        }

    def _generate_vfs(self) -> dict:
        vfs = {}
        root_dir = os.path.join(self._root_dir, 'fs')
        for root, dirs, files in os.walk(root_dir, topdown=False):
            real_root = root
            if root.startswith(root_dir):
                root = root.replace(root_dir, '', 1)
            for name in dirs:
                real_name = name
                if name.startswith(root_dir):
                    name = name.replace(root_dir, '', 1)

                path = root + self._sep + name
                if path[0] != self._sep:
                    path = self._sep + path
                if path not in vfs:
                    vfs[path] = {
                        'type': VFS.INODE_TYPE_DIRECTORY,
                        **self._get_perms(os.path.realpath(os.path.join(real_root, real_name)))
                    }
                if 'files' not in vfs[path]:
                    vfs[path]['files'] = []
                
                if root not in vfs:
                    vfs[root] = {
                        'type': VFS.INODE_TYPE_DIRECTORY,
                        **self._get_perms(os.path.realpath(os.path.join(real_root, real_name)))
                    }
                if 'files' not in vfs[root]:
                    vfs[root]['files'] = []
                vfs[root]['files'].append(name)
            
            for name in files:
                real_name = name
                if name.startswith(root_dir):
                    name = name.replace(root_dir, '', 1)
                
                path = root + self._sep + name
                if path[0] != self._sep:
                    path = self._sep + path
                if path not in vfs:
                    vfs[path] = {
                        'type': VFS.INODE_TYPE_FILE,
                        'real_path': os.path.realpath(os.path.join(real_root, real_name)),
                        **self._get_perms(os.path.realpath(os.path.join(real_root, real_name)))
                    }
                
                if root not in vfs:
                    vfs[root] = {
                        'type': VFS.INODE_TYPE_DIRECTORY,
                        **self._get_perms(os.path.realpath(real_root))
                    }
                if 'files' not in vfs[root]:
                    vfs[root]['files'] = []
                vfs[root]['files'].append(name)
        if "" in vfs:
            vfs[self._sep] = vfs[""]
            del vfs[""]
        return vfs
    
    def _get_perms(self, path: str) -> dict:
        st = os.stat(path)
        return {
            'mode': st.st_mode,
            'size': st.st_size,
            'atime': st.st_atime_ns,
            'ctime': st.st_ctime_ns,
            'mtime': st.st_mtime_ns
        }

    def _add_imports(self, vfs: dict) -> None:
        root_dir = os.path.join(self._root_dir, 'imports')
        for root, _, files in os.walk(root_dir, topdown=False):
            for file in files:
                if file.endswith('.py'):
                    spec = importlib.util.spec_from_file_location(file[:3], os.path.join(root, file))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, 'info'):
                        info = mod.__getattribute__('info')
                        if info['path'] and info['run']:
                            if isinstance(info['path'], list):
                                self._add_imports_from_list(vfs, info['path'], root, file)
                            else:
                                vfs[info['path']]['import'] = os.path.realpath(os.path.join(root, file))
    
    def _add_imports_from_list(self, vfs: dict, paths: list, root: str, file: str):
        known_good_path = None
        for path in paths:
            if path in vfs:
                known_good_path = path
                break
        if not known_good_path:
            print(f'[-] Failed Adding Import: No Valid Paths ({paths})')
            return
        
        for path in paths:
            if path not in vfs:
                d, f = path.rsplit(self._sep, 1)
                if d not in vfs or vfs[d]['type'] != VFS.INODE_TYPE_DIRECTORY:
                    print(f'[-] Failed Adding Import: Not Valid Directory ({path})')
                    return
                if f not in vfs[d]['files']:
                    vfs[d]['files'].append(f)
                vfs[path] = copy.copy(vfs[known_good_path])
            vfs[path]['import'] = os.path.realpath(os.path.join(root, file))

if __name__ == '__main__':
    mkfs = MakeVFS('../var/linux_fs')
    vfs = mkfs.generate()
    with open('../etc/linux_vfs.json', 'w') as f:
        json.dump(vfs, f, indent=4, sort_keys=True)