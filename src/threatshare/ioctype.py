
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
    FILE_CREATE = 3

    '''
    {
        'path': VFSPath
    }
    '''
    DIRECTORY_DELETE = 4

    '''
    {
        path: VFSPath
    }
    '''
    DIRECTORY_CREATE = 5

    '''
    {
        'path': VFSPath,
        'real_path': PathToUnderlyingFile,
        'bytes_read': IntBytesRead
    }
    '''
    FILE_READ = 6

    '''
    {
        'path': VFSPath,
        'real_path': PathToUnderlyingFile,
        'new_size': IntSizeAfterWrite,
        'old_size': IntSizeBeforeWrite,
        'overwrite': BoolOverwriteContents
    }
    '''
    FILE_WRITE = 7

    '''
    {
        source_path: VFSPath,
        destination_path: VFSPath
    }
    '''
    FILE_COPY = 8

    '''
    {
        source_path: VFSPath,
        destination_path: VFSPath
    }
    '''
    FILE_MOVE = 9

    '''
    {
        path: VFSPath,
        old_mode: IntStatMode,
        new_mode: IntStatMode
    }
    '''
    FILE_PERMISSION_CHANGE = 10

    '''
    {
        commands: ListCommands
    }
    '''
    SHELL_COMMANDS = 20

    '''
    {
        username: StrUsername,
        password: StrPassword
    }
    '''
    NETWORK_AUTHENTICATION = 50

    '''
    {
        method: HTTPMethod,
        path: URIPath,
        http_version: HTTPVersion,
        headers: ListHeaderTuples
    }
    '''
    HTTP_REQUEST = 60

    '''
    {
        content: StrContents
    }
    '''
    HTTP_REQUEST_DATA = 61