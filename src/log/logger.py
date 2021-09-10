
class Logger(object):
    def __init__(self):
        pass
    def debug(self, msg: str):
        print(f'[DEBUG] - {msg}')
    def info(self, msg: str):
        print(f'[INFO]  - {msg}')
    def error(self, msg: str):
        print(f'[ERROR] - {msg}')
    def fatal(self, msg: str):
        print(f'[FATAL] - {msg}')
        import os; os._exit(1)

logger: Logger = Logger()