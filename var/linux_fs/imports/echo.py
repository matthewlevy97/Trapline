from services.bash.handler import BashHandler

def run(bash: BashHandler, executable: str, args: list) -> int:
    suppress_trailing = False
    interpret_backslash = False

    for arg in args:
        if arg[0] == '-':
            pop_arg = False
            for miniarg in arg[1:]:
                if miniarg == 'n':
                    suppress_trailing = True
                    pop_arg = True
                elif miniarg == 'e':
                    interpret_backslash = True
                    pop_arg = True
                elif miniarg == 'E':
                    interpret_backslash = False
                    pop_arg = True
                else:
                    pop_arg = False
                    break
            if pop_arg:
                args.remove(arg)
    
    output = ' '.join(args)
    if interpret_backslash:
        output = output.replace('\\t', '    ')
        output = output.replace('\\n', '\n')
        output = output.replace('\\r', '\r')
        output = output.replace('\\\\', '\\')

        pos = output.find('\\x')
        while pos >= 0:
            pos += 2
            val = ''
            for i in range(3):
                if pos+i >= len(output):
                    break

                if output[pos+i] in '0123456789ABCDEFabcdef':
                    val += output[pos+i]
                else:
                    break
            
            if len(val) > 0:
                output = output.replace(f'\\x{val}', str(chr(int(val, 16))), 1)
            else:
                output = output.replace(f'\\x', 'x', 1)
            pos = output.find('\\x')
    
    bash.stdout(output.encode('utf-8'), suppress_trailing)
    return 0

info = {
    'command': 'echo',
    'path': ['/usr/bin/echo', '/bin/echo'],
    'help_long': '',
    'help_short': '',
    'run': run
}