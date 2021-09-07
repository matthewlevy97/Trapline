
class CommandParser(object):
    def __init__(self):
        self._tokens = []
        self._data = ''
        self._error_message = None
    
    def feed(self, data: str) -> None:
        self._data += data
        self._tokenize()

    '''
    command:
    {
        executable: XXX,
        args: [],
        pipe: {
            ...command...
        },
        conditional: [
            {
                type: AND|OR,
                ...command...
            }
        ]
        redirect: {
            stdout: {
                file: filename,
                overwrite: bool
            },
            stderr: {
                file: filename,
                overwrite: bool
            },
            stdin: {
                file: filename
            }
        }
    }
    '''
    def parse(self) -> list:
        self._error_message = None
        commands = []
        while len(self._tokens) and self._error_message == None:
            command = self._parse()
            commands.append(command)
        return (commands, self._error_message)
    
    def _parse(self):
        command = {
            'executable': None,
            'args': []
        }

        while len(self._tokens) > 0:
            token = self._tokens.pop(0)

            if token == None or token == ';':
                # End of Command
                return command
            elif token == '|':
                # Pipe
                command['pipe'] = self._parse()
                return command
            elif token == '&':
                # TODO: Background Command
                self._error_message = 'Unsupported token `&\''
                return None
            elif token == '||':
                # Boolean Logic
                command['conditional_or'] = self._parse()
                return command
            elif token == '&&':
                # Boolean Logic
                command['conditional_and'] = self._parse()
                return command
            elif token == '<':
                # Redirect File STDIN
                file_name = self._tokens.pop(0)
                if not file_name or file_name[0] in '|<>\0\\:*?"' or \
                    file_name == '.' or file_name == '..':
                    self._tokens.insert(0, file_name)
                    self._tokens.insert(0, token)
                    if file_name == None:
                        file_name = 'newline'
                    self._error_message = f'syntax error near unexpected token `{file_name}\''
                    return None
                
                if 'redirect' not in command:
                    command['redirect'] = {}
                command['redirect']['stdin'] = {
                    'file': file_name
                }
            elif token.find('>') >= 0:
                # Redirect Output
                pos = token.find('>')
                fd = token[:pos]
                token2 = token[pos:]
                if fd and fd == '2':
                    redir_str = 'stderr'
                else:
                    redir_str = 'stdout'
                
                if token2 == '>':
                    append = False
                elif token2 == '>>':
                    append = True
                else:
                    self._tokens.insert(0, token)
                    self._error_message = f'syntax error near unexpected token `{token2[2:]}\''
                    return None
                
                file_name = self._tokens.pop(0)
                if not file_name or file_name[0] in '|<>\0\\:*?"' or \
                    file_name == '.' or file_name == '..':
                    self._tokens.insert(0, file_name)
                    self._tokens.insert(0, token)
                    if file_name == None:
                        file_name = 'newline'
                    self._error_message = f'syntax error near unexpected token `{file_name}\''
                    return None
                
                if 'redirect' not in command:
                    command['redirect'] = {}
                command['redirect'][redir_str] = {
                    'file': file_name,
                    'overwrite': False if append else True
                }
            elif command['executable'] == None:
                command['executable'] = token
            else:
                command['args'].append(token)

        return command
    
    # Handle '\\'
    '''
    End of Line signified by None value
    '''
    def _tokenize(self) -> list:
        base = 0
        end = 0
        
        while end < len(self._data):
            if (self._data[end] == '"' or self._data[end] == '\'') and not (end > 0 and self._data[end-1] == '\\'):
                # Save previous token
                token = self._data[base:end]
                if token:
                    self._tokens.append(token)
                
                # Get quoted token
                base = end
                end = self._data.find(self._data[base], end+1)
                while self._data[end-1] == '\\':
                    end = self._data.find(self._data[base], end+1)
                self._tokens.append(self._data[base+1:end])

                # Clear token selection
                base = end+1
            elif self._data[end] == ' ' or self._data[end] == '\t':
                # Save token
                token = self._data[base:end]
                if token:
                    self._tokens.append(token)
                base = end+1
            elif self._data[end] == '\r' or self._data[end] == '\n':
                # Save token
                token = self._data[base:end]
                if token:
                    self._tokens.append(token)
                self._tokens.append(None)
                base = end+1
            elif self._data[end] == '|' or self._data[end] == '&' or \
                self._data[end] == '<' or self._data[end] == ';':
                # Save token
                token = self._data[base:end]
                if token:
                    self._tokens.append(token)
                
                base = end
                while self._data[end+1] == self._data[base]:
                    end += 1
                self._tokens.append(self._data[base:end+1])

                # Clear token selection
                base = end+1
            elif self._data[end] in '0123456789':
                tmp = end + 1
                while self._data[tmp+1] in '0123456789':
                    tmp += 1
                if self._data[tmp] == '>':
                    # Save previous token
                    token = self._data[base:end]
                    if token:
                        self._tokens.append(token)
                    
                    base = end
                    end = tmp
                    while self._data[end+1] == '>':
                        end += 1
                    self._tokens.append(self._data[base:end+1])

                    # Clear token selection
                    base = end+1
                else:
                    end = tmp
            end += 1

        if self._error_message == None:
            self._data = self._data[end:]
        return self._tokens
