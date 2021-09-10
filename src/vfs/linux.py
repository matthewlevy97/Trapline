
from vfs.vfs import VFS

class LinuxVFS(VFS):
    def __init__(self) -> None:
        super().__init__("etc/linux_vfs.json")