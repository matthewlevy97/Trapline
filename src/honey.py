
from log.logger import logger
from net.manager import NetManager
from util.config import Config
import argparse
import atexit
import importlib
import os
import pwd
import signal
import socket
import sys
import time

class Honey(object):
    def __init__(self, config_file_path: str = None, daemonize: bool = False, pidfile: str = 'honey.pid'):
        self._config_file_path = config_file_path
        self._daemonize = daemonize
        self._pidfile = pidfile if pidfile != None else 'honey.pid'
        self._root_directory = os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))[0]
        os.chdir(self._root_directory)
        self._load_config()
    
    def start(self):
        if self._daemonize:
            try:
                with open(self._pidfile, 'r') as pf:
                    pid = int(pf.read().strip())
            except IOError:
                pid = None
            if pid:
                sys.stderr.write(f'pidfile {self._pidfile} already exists.\nDaemon already running?\n')
                return
            
            self.daemonize()
        self.run()
    
    def stop(self):
        try:
            with open(self._pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if not pid:
            if self._daemonize:
                sys.stderr.write(f'pidfile {self._pidfile} does not exists.\nDaemon not running?\n')
            return
        
        try:
            while True:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            e = str(err.args)
            if e.find('No such process') >= 0:
                if os.path.exists(self._pidfile):
                    os.remove(self._pidfile)
            else:
                return

    def restart(self):
        if os.path.exists(self._pidfile):
            self.stop()
        self.start()
    
    def daemonize(self) -> None:
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as err:
            sys.exit(1)
        
        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as err:
            sys.exit(1)
        
        sys.stdout.flush()
        sys.stderr.flush()

        si = open(os.devnull, 'r')
        so = open(self._log_file_path, 'a+')
        se = open(self._log_file_path, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        pid = str(os.getpid())
        with open(self._pidfile, 'w+') as f:
            f.write(f'{pid}\n')
        atexit.register(self._delpid)
    
    def _delpid(self):
        if os.path.exists(self._pidfile):
            os.remove(self._pidfile)
        os.killpg(0, signal.SIGTERM)

    def run(self):
        if os.getuid() == 0 or os.getgid() == 0:
            if not self._demote_username:
                sys.stderr.write('Must have a username to demote to if running as root!\n')
                sys.exit(1)
        
        self.server_manager = NetManager()

        self._setup_system()
        self._load_services()

        if os.getuid() == 0 or os.getgid() == 0:
            user = pwd.getpwnam(self._demote_username)
            os.setgid(user.pw_gid)
            os.setuid(user.pw_uid)
        logger.info(f'Running as [UID: {os.getuid()}, GID: {os.getgid()}]')
        self.server_manager.run()
        sys.exit(0)

    def _load_config(self) -> None:
        Config.set_config_path(self._config_file_path)
        settings = Config.get('settings')

        if not settings:
            sys.stderr.write('Config file missing "settings" entry')
            sys.exit(1)
        
        self._socket_timeout = settings.get('sockettimeout', 120)
        self._daemonize = settings.get('daemonize', self._daemonize)
        self._demote_username = settings.get('demote_username', None)
        self._log_file_path = settings.get('log_file_path', os.devnull)

    def _setup_system(self) -> None:
        socket.setdefaulttimeout(self._socket_timeout)

    def _load_services(self) -> None:
        services = Config.get('services')
        if not services:
            logger.fatal(f'"services" not found in config file')
        for service in services:
            self._load_service(service)

    def _load_service(self, service):
        service_name = service.pop('name')
        mod = importlib.import_module(f'services.{service_name}')
        if not hasattr(mod, 'metadata'):
            logger.fatal(f'{service_name} has no "metadata" defined')
        
        metadata = mod.__getattribute__('metadata')
        if 'server' not in metadata or not metadata['server']:
            logger.fatal(f'{service_name} has no "server" defined')
        
        self.server_manager.add_server(metadata['server'](**service))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Honeypot Control')
    parser.add_argument('-d', '--daemonize', dest='daemonize', action='store_true',
                        help='Daemonize the honeypot runner')
    parser.add_argument('--config_file', dest='path', action='store',
                        default=None, help='Path to config file')
    parser.add_argument('--start', dest='action', action='store_const',
                        const=0, help='Start the honeypots')
    parser.add_argument('--stop', dest='action', action='store_const',
                        const=1, help='Stop the honeypots')
    parser.add_argument('--restart', dest='action', action='store_const',
                        const=2, help='Restart the honeypots')
    
    args = parser.parse_args()
    honey = Honey(args.path, args.daemonize)

    if args.action == 0:
        honey.start()
    elif args.action == 1:
        honey.stop()
    elif args.action == 2:
        honey.restart()