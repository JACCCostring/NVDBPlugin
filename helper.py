import logging
from pathlib import Path

class Logger:
    def __init__(self):
        # Create a logger
        self.logger = logging.getLogger("__name__")
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