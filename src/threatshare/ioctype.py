
class IOCType(object):
    '''
    {
        'protocol': StrServerProtocol,
        'port': IntServerPorts
    }
    '''
    CONNECTION_TYPE = 0

    '''
    {
        'binary': UnderlyingFileName,
        'path': VFSPath
    }
    '''
    BINARY_FILE = 1

    '''
    {
        'path': VFSPath
    }
    '''
    FILE_DELETE = 2

    '''
    {
        'path': VFSPath
    }
    '''
    DIRECTORY_DELETE = 3

    '''
    {
        'path': VFSPath,
        'real_path': PathToUnderlyingFile,
        'bytes_read': IntBytesRead
    }
    '''
    FILE_READ = 4

    '''
    {
        'path': VFSPath,
        'real_path': PathToUnderlyingFile,
        'new_size': IntSizeAfterWrite,
        'old_size': IntSizeBeforeWrite,
        'overwrite': BoolOverwriteContents
    }
    '''
    FILE_WRITE = 5