import hashlib
from threatshare.ioctype import IOCType
from util.http.basehandler import HTTPBaseHandler
from util.http.status import HTTPStatus
import json

class ExploitPaths(object):
    def __init__(self, handler: HTTPBaseHandler):
        self.handler = handler
        
        self._stdout = ''
        self._stderr = ''
        self._exit_code = 0

        self.known_paths = {
            '/uploaded_shell': self._uploaded_shell,
            '/robots.txt': self._robots_txt,
            '/index.php': self._index_php,
            '/cgi-bin/spboard/board.cgi': self._spboard_v4_5,
            '/picsdesc.xml': self._realtek_sdk_miniigd_upnp_soap_rce,
            '/wanipcn.xml': self._realtek_sdk_miniigd_upnp_soap_rce,
            '/setup.cgi': self._setup_cgi,
            '/GponForm/diag_Form': self._gpon_router_auth_bypass,
            '/diag.html': self._gpon_router_auth_bypass,
            '/Autodiscover/Autodiscover.xml': self._proxy_logon,
            '/mapi/emsmdb/': self._proxy_logon,
            '/config/getuser': self._config_getuser,
            '/solr/admin/info/system': self._apache_solr_8_2_0_rce,
            '/select': self._apache_solr_8_2_0_rce,
            '/wp-content/plugins/wp-file-manager/readme.txt': self._wp_file_manager,
            '/wp-content/plugins/wp-file-manager/lib/php/connector.minimal.php': self._wp_file_manager,
            '/_ignition/execute-solution': self._ignition_2_5_1_rce,
            '/actuator/health': self._spring_boot,
            '/boaform/admin/formLogin': self._optilink_ont1gew_gpon_rce,
            '/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php': self._php_unit_rce,
        }

    def handle(self) -> bool:
        if self.handler.path in self.known_paths:
            return self.known_paths[self.handler.path]()
        return False
    
    def _uploaded_shell(self) -> bool:
        # All shell uploads should point to this path
        return False

    def _rce(self, cmd: str) -> int:
        if cmd:
            self._stdout, self._stderr, self._exit_code = self.handler.bash.handle_lines([f'{cmd}\r\n'])
            self._stdout = self._stdout.decode('latin-1')
            self._stderr = self._stderr.decode('latin-1')

        self.handler.add_content(
            self.handler.load_template(
                'http/command_execution.html',
                stdout=self._stdout, stderr=self._stderr, exit_code=self._exit_code))
        return self._exit_code

    def _robots_txt(self) -> bool:
        self.handler.add_content(self.handler.load_template('http/robots.txt'), 'text/plain')
        self.handler.send_response(HTTPStatus.OK)
        return True
    
    def _index_php(self) -> bool:
        param_function = self.handler.parameters.get('function', [])
        if param_function and param_function[0] == 'call_user_func_array':
            # ThinkPHP5 RCE
            func = self.handler.parameters.get('vars[0]', [])
            param = self.handler.parameters.get('vars[1][]', [])
            if func == 'md5':
                self.handler.add_content(hashlib.md5(param.encode('latin-1')).hexdigest())
        else:
            return False
        
        self.handler.send_response(HTTPStatus.OK)
        return True

    def _spboard_v4_5(self) -> bool:
        cmd = self.handler.parameters.get('file', None)
        if cmd:
            cmd = cmd[0].strip('|')
            if len(cmd) > 0:
                self._rce(cmd)
                self.handler.add_header('Content-Disposition', 'attachment; filename="board.cgi"')
                self.handler.send_response(HTTPStatus.OK)
                return True
        return False
    
    def _realtek_sdk_miniigd_upnp_soap_rce(self) -> bool:
        self.handler.server_name = 'miniupnpd/1.0 UPnP/1.0'
        if self.handler.path == '/wanipcn.xml' and self.handler.command == 'POST':
            pos = self.handler.contents.find('NewInternalClient')
            if pos >= 0:
                cmd = self.handler.contents[pos + len('NewInternalClient'):]
                cmd = cmd[:cmd.find('NewInternalClient')]
                # TODO: Handle parsing and executing command
        return False
    
    def _setup_cgi(self) -> bool:
        # Netgear DGN1000 1.1.00.48 'setup.cgi' RCE
        if self.handler.command == 'GET':
            self.handler.add_header('WWW-Authenticate', 'DGN1000')
            cmd = self.handler.parameters.get('cmd', None)
            if cmd:
                self._rce(cmd[0])
                self.handler.send_response(HTTPStatus.OK)
                return True
        return False
    
    def _gpon_router_auth_bypass(self) -> bool:
        if self.handler.path == '/GponForm/diag_Form':
            params = self.handler.parameters
            if 'dest_host' not in params:
                params = self.handler.decode_form_data(self.handler.contents)
                if 'dest_host' not in params:
                    return False
            cmd = params['dest_host'][0]
            if cmd[0] == '`':
                cmd = cmd[1:]
                cmd = cmd[:cmd.find('`')]
            self._rce(cmd)
            self.handler.send_response(HTTPStatus.OK)
        else:
            self._rce(None)
            self.handler.send_response(HTTPStatus.OK)
        return True
    
    def _proxy_logon(self) -> bool:
        data = self.handler.contents
        ret = None
        if self.handler.path == 'Autodiscover/Autodiscover.xml':
            if self.handler.headers.get('Content-Type', '').find('/xml') > 0:
                if data.startswith('<!DOCTYPE') and data.find('SYSTEM "'):
                    ssrf = data[data.find('SYSTEM "') + len('SYSTEM "'):]
                    ssrf = ssrf[:ssrf.find('"')]
                    if ssrf.startswith('file://'):
                        vfs = self.handler.bash.get_vfs()
                        response_file = vfs.read_file(ssrf[len('file://'):])
                        dde = data[:data.find(' SYSTEM')].strip().split()[-1]
                        ret = data.replace(f'&{dde};', response_file)
                
                # ProxyLogon
                if data.find('<EMailAddress>') > 0:
                    if not ret:
                        ret = ''
                    ret += '<LegacyDN>ProxyLogonLegacyDN</LegacyDN>'
                    ret += '<Server>ProxyLogonServer</Server>'
        elif self.handler.path == '/mapi/emsmdb/':
            mailboxID = self.handler.parameters.get('mailboxID', [])
            if mailboxID and mailboxID[0] == 'ProxyLogonServer':
                ret = 'with SID (S-1-5-20)'
        if ret:
            self.handler.add_content(ret)
            self.handler.send_response(HTTPStatus.OK)
            return True
        return False
    
    def _config_getuser(self) -> bool:
        # CVE-2020-25078: DCS-2530L Leaked Admin
        self.handler.add_content('name=admin\r\npass=admin\r\npriv=1\r\n')
        self.handler.send_response(HTTPStatus.OK)
        return True
    
    def _apache_solr_8_2_0_rce(self) -> bool:
        if self.handler.command != 'GET':
            return False
        
        if self.handler.path == '/solr/admin/info/system':
            output = {
                'system': {
                    'name': 'ApacheSolr',
                    'uname': 'Linux',
                    'version': '8.2.0'
                }
            }
            self.handler.add_content(json.dumps(output))
            self.handler.send_response(HTTPStatus.OK)
        elif self.handler.path == '/select':
            exec = self.handler.parameters.get('v.template.custom', [])
            if exec:
                pos = exec[0].find('exec(')
                if pos > 0:
                    cmd = exec[0][pos + len('exec('):]
                    cmd = cmd[:cmd.find('))') - 1]
                    self._rce(cmd)
                    self.handler.send_response(HTTPStatus.OK)
        else:
            return False
        return True
    
    def _wp_file_manager(self) -> bool:
        # CVE-2020-25213
        if self.handler.path == '/wp-content/plugins/wp-file-manager/readme.txt':
            self.handler.add_content('== Changelog ==\r\n6.5')
        elif self.handler.path == '/wp-content/plugins/wp-file-manager/lib/php/connector.minimal.php':
            if self.handler.parameters.get('cmd', None) == None:
                self.handler.add_content(json.dumps({
                    'error': ['errUnknownCmd']
                }))
            else:
                upload = self.handler.parameters.get('upload[]', [])
                if upload:
                    self.handler._threat_session.add_binary(upload[0])
                self.handler.add_content('upload.added[0].url = /uploaded_shell')
        else:
            return False
        
        self.handler.send_response(HTTPStatus.OK)
        return True
    
    def _ignition_2_5_1_rce(self) -> bool:
        # TODO: Need better attacks before populating this function
        return False
    
    def _spring_boot(self) -> bool:
        if self.handler.path == '/actuator/health':
            self.handler.add_content(json.dumps({
                "status" : "UP",
                "components" : {
                    "broker" : {
                        "status" : "UP",
                        "components" : {
                            "us1" : {
                                "status" : "UP",
                                "details" : {
                                    "version" : "1.0.2"
                                }
                            },
                            "us2" : {
                                "status" : "UP",
                                "details" : {
                                    "version" : "1.0.4"
                                }
                            }
                        }
                    },
                    "db" : {
                        "status" : "UP",
                        "details" : {
                            "database" : "H2",
                            "validationQuery" : "isValid()"
                        }
                    },
                    "diskSpace" : {
                        "status" : "UP",
                        "details" : {
                            "total" : 194687758336,
                            "free" : 38642937856,
                            "threshold" : 10485760,
                            "exists" : True
                        }
                    }
                }
            }))
        else:
            return False
        
        self.handler.send_response(HTTPStatus.OK)
        return True
    
    def _optilink_ont1gew_gpon_rce(self) -> bool:
        if self.handler.path == '/boaform/admin/formLogin':
            username = self.handler.parameters.get('username', [])
            password = self.handler.parameters.get('psd', [])

            if not username:
                username = None
            else:
                username = username[0]
            if not password:
                password = None
            else:
                password = password[0]
            
            self.handler._threat_session.add_ioc(IOCType.NETWORK_AUTHENTICATION, {
                'username': username,
                'password': password
            })
            self.handler.add_content('Login Successful')
        else:
            return False

        self.handler.send_response(HTTPStatus.OK)
        return True
    
    def _php_unit_rce(self) -> bool:
        # CVE-2017-9841
        content = self.handler.contents
        if not content:
            return False
        
        if content.find('md5(') >= 0:
            md5 = content[content.find('md5(') + 5:] # Remove quote
            md5 = md5[:md5.find(')') - 1]
            self.handler.add_content(hashlib.md5(md5.encode('latin-1')).hexdigest())
        else:
            return False

        self.handler.send_response(HTTPStatus.OK)
        return True