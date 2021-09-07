
from log.logger import logger
from net.manager import NetManager
import importlib
import json

def main():
    server_manager = NetManager()
    with open('../config.json', 'r') as f:
        config = json.load(f)

    setup_system(config)
    load_services(server_manager, config)
    
    server_manager.run()

def setup_system(config: dict) -> None:
    if 'settings' in config:
        if 'sockettimeout' in config['settings']:
            import socket
            socket.setdefaulttimeout(config['settings']['sockettimeout'])

def load_services(server_manager: NetManager, config: dict) -> None:
    if 'services' not in config:
        logger.fatal(f'"services" not found in config file')
    for service in config['services']:
        _load_service(server_manager, service)

def _load_service(server_manager: NetManager, service):
    service_name = service.pop('name')
    mod = importlib.import_module(f'services.{service_name}')
    if not hasattr(mod, 'metadata'):
        logger.fatal(f'{service_name} has no "metadata" defined')
    
    metadata = mod.__getattribute__('metadata')
    if 'server' not in metadata or not metadata['server']:
        logger.fatal(f'{service_name} has no "server" defined')
    
    server_manager.add_server(metadata['server'](**service))

if __name__ == '__main__':
    main()