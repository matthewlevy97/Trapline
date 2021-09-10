from services.bash.handler import BashHandler
from urllib.parse import urlparse
import random
import requests
import time

def run(bash: BashHandler, executable: str, args: list) -> int:
    quiet_mode = False
    target_url = None
    output_file = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '--no-check-certificate':
            pass
        elif arg == '-q':
            quiet_mode = True
        elif arg == '-O':
            if i+1 < len(args):
                i += 1
                output_file = args[i]
            else:
                bash.stderr(b'wget: option requires an argument -- O')
                return 1
        elif arg == '--help':
            bash.stdout(info['help_long'].encode('utf-8'))
            return 0
        elif arg[0] != '-':
            target_url = arg
        i += 1
    
    if not target_url:
        bash.stdout(info['help_long'].encode('utf-8'))
        return 0

    if target_url.find('://') < 0:
        target_url = 'http://' + target_url

    parsed = urlparse(target_url)
    if not parsed.scheme:
        bash.stderr(f'{target_url}: Scheme missing.'.encode('utf-8'))
        return 1
    if not parsed.hostname:
        bash.stderr(f'{target_url}: Invalid host name.'.encode('utf-8'))
        return 1

    headers = {
        'User-Agent': 'Wget/1.20.3 (linux-gnu)'
    }
    try:
        req = requests.get(url=target_url, headers=headers)
    except:
        req = None

    vfs = bash.get_vfs()
    if not output_file:
        output_file = vfs.basename(parsed.path)[1]
        if not output_file:
            output_file = 'index.html'

    clean_url = f'{parsed.scheme}://{parsed.hostname}'
    output = None
    if not quiet_mode:
        output = f'--{time.strftime("%Y-%m-%d %H:%M:%S")}--  {clean_url}\n'
        output += f'Resolving {clean_url} ({clean_url})... '
        if not req:
            output += f'''failed: nodename nor servname provided, or not known.
wget: unable to resolve host address ‘{clean_url}’'''
            bash.stderr(output.encode('utf-8'))
            return 1
        
        output += 'connected.\nHTTP request sent, awaiting response... '
        if req.status_code == 200:
            output += '200 OK\n'
        elif req.status_code == 404:
            output += '404 File not found\n'
        
        output += f'Length: unspecified [{req.headers["Content-Type"]}]\n'
        output += f'Saving to: ‘{"STDOUT" if output_file == "-" else output_file}’\n\n'
        output += f'{"STDOUT" if output_file == "-" else output_file}'

        length = len(req.content)
        if length > 1073741824:
            length = f'{length / 1073741824:.1f}G'
        elif length > 1048576:
            length = f'{length / 1048576:.1f}M'
        elif length > 1024:
            length = f'{length / 1024:.1f}K'
        output += ' ' * 11 + '[ <=>' + ' ' * 60 + f']  {length}  --.-KB/s    in 0s\n'
        output += f'{time.strftime("%Y-%m-%d %H:%M:%S")} ({random.randint(10, 100) / 10} MB/s) - ‘{clean_url}’\n'
        bash.stderr(output.encode('utf-8'))
    
    if output_file != '-':
        if output_file[0] != vfs._sep:
            output_file = vfs.join(bash.get_cwd(), output_file)
        
        file = vfs.lookup(output_file, True)
        if file:
            vfs.write_file(file['path'], req.content, overwrite=True)
    else:
        bash.stdout(req.content)
    return 0

info = {
    'command': 'wget',
    'path': ['/usr/bin/wget', '/bin/wget'],
    'help_long': '''Usage:
    wget [-cqS] [--spider] [-O FILE] [-o LOGFILE] [--header 'HEADER: VALUE'] [-Y on/off]
        [-cqS] [-O FILE] [-o LOGFILE] [-Y on/off] [-P DIR] [-U AGENT]

Retrieve files via HTTP or FTP

        --spider        Only check URL existence: $? is 0 if exists
        --no-check-certificate        Don't validate the server's certificate
        -c                Continue retrieval of aborted transfer
        -q                Quiet
        -P DIR                Save to DIR (default .)
        -S                    Show server response
        -T SEC                Network read timeout is SEC seconds
        -O FILE                Save to FILE ('-' for stdout)
        -o LOGFILE        Log messages to FILE
        -U STR                Use STR for User-Agent header
        -Y on/off        Use proxy''',
    'help_short': '',
    'run': run
}