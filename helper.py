import logging
from pathlib import Path

class Logger:
    def __init__(self):
        # Create a logger
        self.logger = logging.getLogger("__name__")
        self.logger.setLevel(logging.DEBUG)
        self.format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    def write_log(self, type):
        if type.lower() == "console":
            # Logging to console
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(self.format)
            self.logger.addHandler(console_handler)

        elif type.lower() == "file":
            # logging to file
            home_dir = Path.home()
            log_path = home_dir / 'Documents' / 'log.log'

            file_handler = logging.FileHandler(log_path, mode='w')
            file_handler.setFormatter(self.format)
            self.logger.addHandler(file_handler)
