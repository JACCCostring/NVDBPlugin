# logging 2.0 Singleton Design Pattern

import logging
from pathlib import Path

class Logger:
    # class variable for check if there is instance present
    _instance = None

    def __new__(cls, *args, **kwargs):
        # creates an instance of the logger if one doesn't already exist
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.setup_logger()
        return cls._instance


    def setup_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')


    def log(self, message, output_type):
        if output_type.lower() == "console":
            # logging to console
            self.ch = logging.StreamHandler()
            self.ch.setFormatter(self.format)
            self.logger.addHandler(self.ch)
            self.logger.info(message)
        elif output_type.lower() == "file":
            # logging to file
            home_dir = Path.home()
            log_path = home_dir / 'Documents' / 'log.log'
            self.fh = logging.FileHandler(log_path, mode="a")
            self.fh.setFormatter(self.format)
            self.logger.addHandler(self.fh)
            self.logger.info(message)
        else:
            print("Choose either 'console' or 'file' as log destination")


    def disable_logging(cls):
        #self.logger.disabled = True
       # del cls._instance
        pass




















"""
# logging 1.0
import logging
from pathlib import Path

class Logger:
    def __init__(self):
        # Create a logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.console_handler = None
        self.file_handler = None

    def write_log(self, output_type):
        if output_type.lower() == "console" and self.console_handler is None:
            # Logging to console
            self.console_handler = logging.StreamHandler()
            self.console_handler.setFormatter(self.format)
            self.logger.addHandler(self.console_handler)

        elif output_type.lower() == "file" and self.file_handler is None:
            # logging to file
            home_dir = Path.home()
            log_path = home_dir / 'Documents' / 'log.log'

            self.file_handler = logging.FileHandler(log_path, mode='w')
            self.file_handler.setFormatter(self.format)
            self.logger.addHandler(self.file_handler)
        else:
            print("Choose either 'console' or 'file' as logging destination.")

    def disable_logging(self):
        # disables all logging in the program
        logging.disable(logging.CRITICAL)

        if self.console_handler is not None:
            self.logger.removeHandler(self.console_handler)
            self.console_handler = None
        elif self.file_handler is not None:
            self.logger.removeHandler(self.file_handler)
            self.file_handler = None


    def enable_logging(self):
        if self.console_handler is None:
            self.write_log("console")
        elif self.file_handler is None:
            self.write_log("file")
        else:
            print("Logging is already enabled")
            
            
 """



































