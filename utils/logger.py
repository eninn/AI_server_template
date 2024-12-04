import logging, os

class loggerConfig:
    def __init__(self, logger_name:str, log_dir:str, log_type='file') -> None:
        os.makedirs(log_dir, exist_ok=True)
        formatter = logging.Formatter('[%(asctime)s][%(levelname)s]: %(message)s')
        logging.getLogger(logger_name).handlers.clear()
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)

        if log_type == 'file' or log_type == 'both':
            os.remove(os.path.join(log_dir, f'{logger_name}.log')) if os.path.isfile(os.path.join(log_dir, f'{logger_name}.log')) else None
            file_handler = logging.FileHandler(os.path.join(log_dir, f'{logger_name}.log'))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        if log_type == 'stream' or log_type == 'both':
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

        self.logger.info(f'Logger: {logger_name} is set by {log_type}.')

    def add_info(self, method:str, message:str):
        self.logger.info(f'[{method}]: {message}')

    def add_warning(self, method:str, message:str):
        self.logger.warning(f'[{method}]: {message}')

    def add_error(self, method:str, message:str):
        self.logger.error(f'[{method}]: {message}')

    def add_exception(self, method:str, message:str):
        self.logger.exception(f'[{method}]: {message}')

    def add_critical(self, method:str, message:str):
        self.logger.critical(f'[{method}]: {message}')
