
from net.connectionhandler import ConnectionHandler
from services.bash.handler import BashHandler
from threatshare.ioctype import IOCType
import socket

class TelnetHandler(ConnectionHandler):
    TELNET_IAC       = 255

    '''
    Indicates the demand that the
    other party stop performing,
    or confirmation that you are no
    longer expecting the other party
    to perform, the indicated option.
    '''
    TELNET_DONT      = 254

    '''
    Indicates the request that the
    other party perform, or
    confirmation that you are expecting
    the other party to perform, the
    indicated option.
    '''
    TELNET_DO        = 253

    '''
    Indicates the refusal to perform,
    or continue performing, the
    indicated option.
    '''
    TELNET_WONT      = 252

    '''
    Indicates the desire to begin
    performing, or confirmation that
    you are now performing, the
    indicated option.
    '''
    TELNET_WILL      = 251

    '''Subnegotiation'''
    TELNET_SB        = 250

    '''Go Ahead'''
    TELNET_GA        = 249

    '''Erase Line'''
    TELNET_EL        = 248

    '''Erase Character'''
    TELNET_EC        = 247

    '''Are You There'''
    TELNET_AYT       = 246

    '''Abort Output'''
    TELNET_AO        = 245

    '''Interrupt Process'''
    TELNET_IP        = 244

    '''NVT character BRK'''
    TELNET_BRK       = 243

    '''Data stream protion of a Sync'''
    TELNET_DATA_MARK = 242

    '''No Operation'''
    TELNET_NOP       = 241

    '''End of subnegotiation'''
    TELNET_SE        = 240

    '''New Environment'''
    TELNET_NEW_ENV     = 39
    '''Linemode'''
    TELNET_LINEMODE    = 34
    '''Toggle Flow Control'''
    TELNET_TFC         = 33
    '''Terminal Speed'''
    TELNET_TSPEED      = 32
    '''Negotiation About Window Size'''
    TELNET_NAWS        = 31
    '''Terminal Type'''
    TELNET_TTYPE       = 24
    '''Status'''
    TELNET_STATUS      = 5
    '''Supress Go Ahead'''
    TELNET_SUPPRESS_GA = 3

    def __init__(self, sock: socket.socket, addr):
        super().__init__(sock, addr)
        self._raw_data = b''
        self._data_pos = 0
        self._state = 0
        self._missing_data = False
        self._attempts = 0
        self._attempts_before_success = 1
        self._bash = None
    
    def handle(self) -> None:
        while self._state < 4:
            if self._state == 0:
                response = self._negotiate()
                if response:
                    self._sock.sendall(response)
            elif self._state == 1:
                self._sock.sendall(b'Login: ')
                self._state += 1
            elif self._state == 2:
                self._get_username()
            elif self._state == 3:
                self._get_password()
        
        self._bash = BashHandler(self._sock, self._addr)
        self._bash.handle()
    
    def shutdown(self):
        if self._bash:
            self._bash.shutdown()
        return super().shutdown()
    
    def _negotiate(self) -> bytes:
        ret = b''
        self._raw_data += self._sock.recv(512)

        while self._data_pos < len(self._raw_data) and self._raw_data[self._data_pos] == self.TELNET_IAC:
            if self._data_pos + 1 >= len(self._raw_data):
                self._missing_data = True
                break

            key = self._raw_data[self._data_pos + 1]
            self._data_pos += 2

            if key == self.TELNET_WILL:
                ret += self._will()
            elif key == self.TELNET_WONT:
                ret += self._wont()
            elif key == self.TELNET_DO:
                ret += self._do()
            elif key == self.TELNET_DONT:
                ret += self._dont()
            else:
                # Invalid option
                self._data_pos -= 2
                break
            
            if self._missing_data:
                self._data_pos -= 2
                self._missing_data = False
                break
            else:
                self._raw_data = self._raw_data[self._data_pos:]
                self._data_pos = 0
        
        if not self._missing_data and self._state == 0:
            self._state = 1
        
        return ret
    
    def _will(self) -> bytes:
        if self._data_pos >= len(self._raw_data):
            self._missing_data = True
            return b''
        option = self._raw_data[self._data_pos]
        self._data_pos += 1

        if option == self.TELNET_TTYPE:
            return bytes([self.TELNET_IAC, self.TELNET_DO, option])
        elif option == self.TELNET_NAWS:
            return bytes([self.TELNET_IAC, self.TELNET_DONT, option])
        elif option == self.TELNET_TSPEED:
            return bytes([self.TELNET_IAC, self.TELNET_DONT, option])
        elif option == self.TELNET_TFC:
            return bytes([self.TELNET_IAC, self.TELNET_DONT, option])
        elif option == self.TELNET_LINEMODE:
            return bytes([self.TELNET_IAC, self.TELNET_DONT, option])
        elif option == self.TELNET_NEW_ENV:
            return bytes([self.TELNET_IAC, self.TELNET_DO, option])

        return b''
    
    def _wont(self) -> bytes:
        if self._data_pos >= len(self._raw_data):
            self._missing_data = True
            return b''
        option = self._raw_data[self._data_pos]
        self._data_pos += 1

        if option == self.TELNET_TTYPE:
            return bytes([self.TELNET_IAC, self.TELNET_DONT, option])
        elif option == self.TELNET_NAWS:
            return bytes([self.TELNET_IAC, self.TELNET_DONT, option])
        elif option == self.TELNET_TSPEED:
            return bytes([self.TELNET_IAC, self.TELNET_DONT, option])
        elif option == self.TELNET_TFC:
            return bytes([self.TELNET_IAC, self.TELNET_DONT, option])
        elif option == self.TELNET_LINEMODE:
            return bytes([self.TELNET_IAC, self.TELNET_DONT, option])
        elif option == self.TELNET_NEW_ENV:
            return bytes([self.TELNET_IAC, self.TELNET_DONT, option])

        return b''

    def _do(self) -> bytes:
        if self._data_pos >= len(self._raw_data):
            self._missing_data = True
            return b''
        option = self._raw_data[self._data_pos]
        self._data_pos += 1

        if option == self.TELNET_SUPPRESS_GA:
            return bytes([self.TELNET_IAC, self.TELNET_WILL, option])
        elif option == self.TELNET_STATUS:
            return bytes([self.TELNET_IAC, self.TELNET_WONT, option])
        
        return b''

    def _dont(self) -> bytes:
        if self._data_pos >= len(self._raw_data):
            self._missing_data = True
            return b''
        option = self._raw_data[self._data_pos]
        self._data_pos += 1

        if option == self.TELNET_SUPPRESS_GA:
            return bytes([self.TELNET_IAC, self.TELNET_WILL, option])
        elif option == self.TELNET_STATUS:
            return bytes([self.TELNET_IAC, self.TELNET_WONT, option])
        
        return b''
    
    def _get_username(self) -> None:
        username = self.recv_line()
        if username:
            self._username = username
            self._state += 1
            self._sock.sendall(self._line_ending + b'Password: ')
    
    def _get_password(self) -> None:
        password = self.recv_line()
        if password:
            self._sock.sendall(self._line_ending)
            self._password = password
            self._attempts += 1

            self._threat_session.add_ioc(IOCType.NETWORK_AUTHENTICATION, {
                'username': self._username.decode(),
                'password': self._password.decode()
            })
            if self._attempts >= self._attempts_before_success:
                self._state += 1
            else:
                self._state -= 2