import pprint
import logging
from configobj import ConfigObj
from urlparse import parse_qs


class PrettyLog():
    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return pprint.pformat(self.obj)


def initialize_logging(log_file_path, logfmt, datefmt):
    logger = logging.getLogger(__name__)
    logging_level = 10

    handler = logging.FileHandler(log_file_path)
    handler.setLevel(logging_level)

    formatter = logging.Formatter(logfmt, datefmt)

    handler.setFormatter(formatter)

    logger.setLevel(logging_level)
    logger.addHandler(handler)

    return logger


def application(environ, start_response):
    ## Loading configurations
    CONFIG_PATH = "/var/www/ghservice/config.ini"

    config = ConfigObj(CONFIG_PATH, interpolation=False)

    LOG_FILE_PATH = config['Logging']['LOG_PATH']
    LOG_FORMAT = config['Logging']['LOG_FORMAT']
    LOG_DATE_FORMAT = config['Logging']['DATE_FORMAT']
    PVT_DIR_PATH = config['Application']['PVT_DIR']
    ## Finished loading configurations

    logger = initialize_logging(LOG_FILE_PATH, LOG_FORMAT, LOG_DATE_FORMAT)

    logger.info('Started Hanger for "%s"' % environ['HTTP_X_GITHUB_DELIVERY'])

    json_payload = parse_qs(environ['wsgi.input'].read())['payload'][0]

    if json_payload:

        import subprocess
        import sys

        from tempfile import NamedTemporaryFile

        filename = ""

        # Create a temp file with payload and pass it to processor
        with NamedTemporaryFile(delete=False, dir=PVT_DIR_PATH) as f:
            f.write(environ['HTTP_X_GITHUB_EVENT'] + '\n')
            f.write(json_payload + '\n')
            f.flush()

            filename = f.name

            command = [
                sys.executable,
                '/var/www/ghservice/hookprocessor.py',
                filename]

            subprocess.Popen(
                command,
                # stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                # stdin=subprocess.PIPE,
                )

    else:
        logger.error("No json payload was receieved!<br/>\r")
        logger.error(json_payload)

    logger.info("Kan 3ndk hook w ra7 :D")

    status = '200 OK'
    response_headers = [('Content-type', 'text/html')]
    start_response(status, response_headers)

    return ['Done']
