import logging


class WrongLoggingFileNameException(Exception):

    def __init__(self, file_name, message="The filename should ends with .log extension:"):
        self.file_name = file_name
        self.message = message
        super().__init__(f'{self.message} {self.file_name}')


__extensions = '.log'
__log_format = '[%(asctime)s %(filename)s -> %(funcName)s:%(lineno)s] - %(levelname)s %(message)s'


def validate_logger_file(function):
    def wrapper(name: str, file_name: str):
        if file_name.endswith(__extensions):
            return function(name, file_name)
        else:
            raise WrongLoggingFileNameException(file_name)

    return wrapper


@validate_logger_file
def init_logger(logger_name: str, logger_file: str):
    __logger = logging.getLogger(logger_name)
    __logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(f'./{logger_file}')
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)

    formatter = logging.Formatter(__log_format)
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logg
    __logger.addHandler(fh)
    __logger.addHandler(ch)
