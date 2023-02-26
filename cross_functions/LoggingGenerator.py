import logging


class Logger():
    def __init__(self, logger_name):
        self.logger_name = logger_name
        self.logger = logging.getLogger(logger_name)

        self.logger.setLevel(logging.DEBUG)
        # Create a console handler for both loggers
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        # Create a formatter for the console handler
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s:%(funcName)s: %(message)s')
        console_handler.setFormatter(formatter)
        # Add the console handler to the loggers
        self.logger.addHandler(console_handler)

    def get_logger(self):
        logger = logging.getLogger(self.logger_name)
        return logger
